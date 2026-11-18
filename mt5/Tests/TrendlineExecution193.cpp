#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

using std::string;
constexpr long ACCOUNT_TRADE_MODE_DEMO = 0;
constexpr long ACCOUNT_TRADE_MODE_CONTEST = 1;
constexpr long ACCOUNT_TRADE_MODE_REAL = 2;
#include "../Scripts/TrendlineExecution193.mqh"

static_assert(sizeof(long) == 8, "64-bit native test values required");
#define REQUIRE(condition) do { if (!(condition)) throw std::runtime_error("line " + std::to_string(__LINE__) + ": " #condition); } while (false)

const TrendlineAccount193 Demo{true, true, false, ACCOUNT_TRADE_MODE_DEMO, 1, "invented"};

// Isolated fixture storage exercises readback across process restarts. The
// writer owns this path for the test. It is not an MT5 persistence layer.
struct Journal
{
   std::filesystem::path path;

   void save(const TrendlineState193 &state) const
   {
      REQUIRE(ValidTrendlineState193(state));
      auto temporary = path;
      temporary += ".next";
      std::ofstream output(temporary);
      output << state.revision << ' ' << state.last_observation << ' ' << state.last_setup << ' '
             << state.intent_revision << ' ' << state.capacity << ' ' << state.pending << ' '
             << state.held << ' ' << state.required_stop << ' ' << state.intent_units << ' ' << state.intent_stop << ' '
             << state.side << ' ' << state.in_flight << ' ' << state.halted << '\n';
      output.close();
      REQUIRE(output.good());
      std::filesystem::rename(temporary, path);
   }

   TrendlineState193 read() const
   {
      std::ifstream input(path);
      TrendlineState193 state{};
      int action = -1;
      REQUIRE(input >> state.revision >> state.last_observation >> state.last_setup >> state.intent_revision
                    >> state.capacity >> state.pending >> state.held >> state.required_stop >> state.intent_units >> state.intent_stop
                    >> state.side >> action >> state.halted);
      REQUIRE(action >= TRL193_NONE && action <= TRL193_EMERGENCY_CLOSE);
      state.in_flight = static_cast<TrendlineAction193>(action);
      REQUIRE(ValidTrendlineState193(state));
      input >> std::ws;
      REQUIRE(input.eof());
      return state;
   }
};

TrendlineRequest193 entry(long setup = 10, int side = 1)
{
   return {TRL193_ENTRY, setup, 10, 11030, 10, side, true, true, false};
}

TrendlineRequest193 action(TrendlineAction193 kind, long stop = 0)
{
   return {kind, 0, 0, stop, 0, 0, false, false, false};
}

struct Scenario
{
   Journal journal;
   TrendlineSession193 session{};
   int sends = 0;

   Scenario(const std::filesystem::path &path, bool existing = false) : journal{path}
   {
      REQUIRE(StartTrendline193(session, Demo) == TRL193_OK);
      if (!existing) {
         TrendlineState193 initial{};
         InitTrendline193(initial);
         journal.save(initial);
      }
   }

   TrendlineInventory193 inventory(long pending = 0, long held = 0, bool resolve = false, long stop = 11030) const
   {
      const auto saved = journal.read();
      return {saved.last_observation + 1, pending, held, resolve ? saved.intent_revision : 0,
              pending ? 11030 : 0, held ? stop : 0, held, pending || held ? saved.side : 0, true, true};
   }

   TrendlineResult193 observe(const TrendlineInventory193 &observation, const TrendlineAccount193 &account = Demo)
   {
      const auto saved = journal.read();
      TrendlineState193 next{};
      const auto result = ReconcileTrendline193(saved, session, account, observation, next);
      if (result == TRL193_OK) journal.save(next);
      return result;
   }

   TrendlineResult193 prepare(const TrendlineRequest193 &request, TrendlineOffer193 &offer, const TrendlineAccount193 &account = Demo)
   {
      return PrepareTrendline193(journal.read(), session, account, request, offer);
   }

   TrendlineOffer193 stage(const TrendlineRequest193 &request)
   {
      TrendlineOffer193 offer{};
      REQUIRE(prepare(request, offer) == TRL193_OK);
      journal.save(offer.prepared);
      return offer;
   }

   TrendlineResult193 send(TrendlineOffer193 &offer, const TrendlineAccount193 &fresh_account = Demo)
   {
      const auto result = TakeSimulatedOffer193(offer, journal.read(), session, fresh_account);
      if (result == TRL193_OK) ++sends;
      return result;
   }

   void begin(int side = 1)
   {
      REQUIRE(observe(inventory()) == TRL193_OK);
      auto offer = stage(entry(10, side));
      REQUIRE(offer.prepared.intent_units == 10 && offer.prepared.intent_stop == 11030);
      REQUIRE(send(offer) == TRL193_OK);
   }
};

void gate_cases(const std::filesystem::path &path)
{
   REQUIRE(!TrendlineOrdersAvailable193());
   Scenario scenario(path);
   TrendlineOffer193 offer{};
   REQUIRE(scenario.prepare(entry(), offer) == TRL193_RECONCILE);
   const auto flat = scenario.inventory();
   REQUIRE(scenario.observe(flat) == TRL193_OK);
   REQUIRE(scenario.observe(flat) == TRL193_RECONCILE);
   REQUIRE(scenario.prepare(entry(), offer) == TRL193_RECONCILE);
   REQUIRE(scenario.observe(scenario.inventory()) == TRL193_OK);
   for (auto units : {0L, -1L, 11L}) {
      auto request = entry();
      request.units = units;
      REQUIRE(scenario.prepare(request, offer) == TRL193_ENTRY_GATE);
   }
   auto request = entry(); request.level_q = false;
   REQUIRE(scenario.prepare(request, offer) == TRL193_ENTRY_GATE);
   request = entry(); request.qualified = false;
   REQUIRE(scenario.prepare(request, offer) == TRL193_ENTRY_GATE);
   request = entry(); request.entry_paused = true;
   REQUIRE(scenario.prepare(request, offer) == TRL193_ENTRY_GATE);
   request = entry(); request.stop = 0;
   REQUIRE(scenario.prepare(request, offer) == TRL193_ENTRY_GATE);
   request = entry(); request.side = 0;
   REQUIRE(scenario.prepare(request, offer) == TRL193_ENTRY_GATE);
   REQUIRE(scenario.prepare(entry(), offer) == TRL193_OK);
   // A failed or missing write cannot release a simulated send.
   REQUIRE(scenario.send(offer) == TRL193_INTENT_UNVERIFIED);
   REQUIRE(scenario.sends == 0 && scenario.journal.read().capacity == 0);
   REQUIRE(scenario.observe(scenario.inventory()) == TRL193_OK);
   auto changed = entry(); changed.units = 9;
   TrendlineOffer193 different_intent{};
   REQUIRE(scenario.prepare(changed, different_intent) == TRL193_OK);
   offer = scenario.stage(entry());
   REQUIRE(scenario.send(different_intent) == TRL193_INTENT_UNVERIFIED);
   REQUIRE(scenario.send(offer) == TRL193_INTENT_UNVERIFIED);
   REQUIRE(scenario.sends == 0);
   REQUIRE(scenario.observe(scenario.inventory(0, 0, true)) == TRL193_OK);
   REQUIRE(scenario.prepare(entry(), offer) == TRL193_CONSUMED);
   offer = scenario.stage(entry(11));
   auto copy = offer;
   REQUIRE(scenario.send(offer) == TRL193_OK);
   REQUIRE(scenario.send(offer) == TRL193_INTENT_UNVERIFIED);
   REQUIRE(scenario.send(copy) == TRL193_INTENT_UNVERIFIED);
   REQUIRE(scenario.prepare(entry(12), offer) == TRL193_RECONCILE);
   REQUIRE(scenario.observe(scenario.inventory(10, 0, true)) == TRL193_OK);
   REQUIRE(scenario.prepare(entry(12), offer) == TRL193_POSITION_LIMIT);
   REQUIRE(scenario.sends == 1);
}

void account_cases(const std::filesystem::path &path)
{
   for (auto mode : {ACCOUNT_TRADE_MODE_CONTEST, ACCOUNT_TRADE_MODE_REAL, -1L, 77L}) {
      auto different_mode = Demo;
      different_mode.mode = mode;
      TrendlineSession193 session{};
      REQUIRE(StartTrendline193(session, different_mode) == TRL193_ACCOUNT_TYPE);
      REQUIRE(CheckAccount193(session, Demo) == TRL193_ACCOUNT_TYPE);
   }
   auto account = Demo; account.connected = false;
   REQUIRE(AccountGuard193(account) == TRL193_ACCOUNT_UNAVAILABLE);
   account = Demo; account.query_ok = false;
   REQUIRE(AccountGuard193(account) == TRL193_ACCOUNT_UNAVAILABLE);
   account = Demo; account.tester = true;
   REQUIRE(AccountGuard193(account) == TRL193_ACCOUNT_UNAVAILABLE);

   for (auto type : {TRL193_ENTRY, TRL193_TIGHTEN, TRL193_CANCEL, TRL193_EMERGENCY_CLOSE}) {
      const auto request = type == TRL193_ENTRY ? entry() : action(type, 11031);
      constexpr int faults = 7;
      for (int fault = 0; fault < faults; ++fault) {
         Scenario scenario(path);
         if (type == TRL193_ENTRY) {
            REQUIRE(scenario.observe(scenario.inventory()) == TRL193_OK);
         } else {
            scenario.begin();
            auto observation = scenario.inventory(type == TRL193_CANCEL ? 6 : 0, 4, true);
            if (type == TRL193_EMERGENCY_CLOSE) observation.protected_units = 0;
            REQUIRE(scenario.observe(observation) == TRL193_OK);
         }
         auto fresh = Demo;
         TrendlineResult193 expected = TRL193_ACCOUNT_TYPE;
         switch (fault) {
            case 0: fresh.mode = ACCOUNT_TRADE_MODE_REAL; break;
            case 1: fresh.mode = ACCOUNT_TRADE_MODE_CONTEST; break;
            case 2: fresh.mode = -1; break;
            case 3: fresh.login++; expected = TRL193_ACCOUNT_CHANGED; break;
            case 4: fresh.server = "changed"; expected = TRL193_ACCOUNT_CHANGED; break;
            case 5: fresh.connected = false; expected = TRL193_ACCOUNT_UNAVAILABLE; break;
            case 6: fresh.query_ok = false; expected = TRL193_ACCOUNT_UNAVAILABLE; break;
         }
         TrendlineOffer193 denied{};
         REQUIRE(scenario.prepare(request, denied, fresh) == expected);
         auto offer = scenario.stage(request);
         const int before = scenario.sends;
         REQUIRE(scenario.send(offer, fresh) == expected);
         REQUIRE(scenario.send(offer, Demo) == TRL193_INTENT_UNVERIFIED);
         REQUIRE(scenario.sends == before);
         REQUIRE(scenario.journal.read().in_flight == type);
      }
   }
}

void partial_cases(const std::filesystem::path &path)
{
   for (int side : {1, -1}) {
      Scenario scenario(path);
      scenario.begin(side);
      auto partial = scenario.inventory(6, 4, true);
      auto excess = partial; excess.pending = 7;
      REQUIRE(scenario.observe(excess) == TRL193_INVENTORY);
      auto opposite = partial; opposite.side = -side;
      REQUIRE(scenario.observe(opposite) == TRL193_INVENTORY);
      auto foreign = partial; foreign.owned = false;
      REQUIRE(scenario.observe(foreign) == TRL193_INVENTORY);
      REQUIRE(scenario.observe(partial) == TRL193_OK);
      REQUIRE(!scenario.journal.read().halted);
      TrendlineOffer193 denied{};
      REQUIRE(scenario.prepare(action(TRL193_TIGHTEN, 11030 + side), denied) == TRL193_PROTECTION);
      auto cancel = scenario.stage(action(TRL193_CANCEL));
      REQUIRE(cancel.prepared.intent_units == 6 && scenario.send(cancel) == TRL193_OK);
      REQUIRE(scenario.observe(scenario.inventory(6, 4)) == TRL193_OK);
      REQUIRE(scenario.prepare(action(TRL193_CANCEL), denied) == TRL193_RECONCILE);
      REQUIRE(scenario.observe(scenario.inventory(0, 4, true)) == TRL193_OK);
      REQUIRE(scenario.prepare(action(TRL193_TIGHTEN, 11030 - side), denied) == TRL193_PROTECTION);
      REQUIRE(scenario.prepare(action(TRL193_TIGHTEN, 11030), denied) == TRL193_PROTECTION);
      auto tighten = scenario.stage(action(TRL193_TIGHTEN, 11030 + side));
      REQUIRE(tighten.prepared.intent_units == 4 && scenario.send(tighten) == TRL193_OK);
      // A reconciled rejection leaves the previously verified stop in place.
      REQUIRE(scenario.observe(scenario.inventory(0, 4, true)) == TRL193_OK);
      REQUIRE(scenario.journal.read().required_stop == 11030 && !scenario.journal.read().halted);
      tighten = scenario.stage(action(TRL193_TIGHTEN, 11030 + side));
      REQUIRE(scenario.send(tighten) == TRL193_OK);
      REQUIRE(scenario.observe(scenario.inventory(0, 4, true, 11030 + side)) == TRL193_OK);
      REQUIRE(scenario.journal.read().required_stop == 11030 + side);
      REQUIRE(scenario.prepare(action(TRL193_TIGHTEN, 11030), denied) == TRL193_PROTECTION);
   }
}

void emergency_cases(const std::filesystem::path &path)
{
   {
      Scenario pending(path);
      pending.begin();
      auto unprotected_order = pending.inventory(6, 4, true);
      unprotected_order.pending_stop = 0;
      REQUIRE(pending.observe(unprotected_order) == TRL193_OK);
      REQUIRE(pending.journal.read().halted);
   }
   Scenario scenario(path);
   scenario.begin();
   auto uncovered = scenario.inventory(6, 4, true);
   uncovered.protected_units = 3;
   REQUIRE(scenario.observe(uncovered) == TRL193_OK);
   REQUIRE(scenario.journal.read().halted);
   TrendlineOffer193 denied{};
   REQUIRE(scenario.prepare(entry(11), denied) == TRL193_HALTED);
   REQUIRE(scenario.prepare(action(TRL193_EMERGENCY_CLOSE), denied) == TRL193_PROTECTION);
   auto cancel = scenario.stage(action(TRL193_CANCEL));
   REQUIRE(cancel.prepared.intent_units == 6 && scenario.send(cancel) == TRL193_OK);
   uncovered = scenario.inventory(0, 4, true);
   uncovered.position_stop = 0;
   REQUIRE(scenario.observe(uncovered) == TRL193_OK);
   auto emergency = scenario.stage(action(TRL193_EMERGENCY_CLOSE));
   REQUIRE(emergency.prepared.intent_units == 4 && scenario.send(emergency) == TRL193_OK);
   REQUIRE(scenario.observe(scenario.inventory(0, 4)) == TRL193_OK);
   REQUIRE(scenario.prepare(action(TRL193_EMERGENCY_CLOSE), denied) == TRL193_RECONCILE);
   REQUIRE(scenario.observe(scenario.inventory(0, 0, true)) == TRL193_OK);
   REQUIRE(scenario.journal.read().halted && scenario.journal.read().capacity == 0);
   Scenario restarted(path, true);
   REQUIRE(restarted.observe(restarted.inventory()) == TRL193_OK);
   REQUIRE(restarted.prepare(entry(11), denied) == TRL193_HALTED);
   REQUIRE(restarted.sends == 0);
}

void stop_at_intent(const std::filesystem::path &path, bool send_before_exit)
{
   Scenario scenario(path);
   REQUIRE(scenario.observe(scenario.inventory()) == TRL193_OK);
   auto offer = scenario.stage(entry());
   REQUIRE(scenario.journal.read().intent_revision == offer.prepared.revision);
   REQUIRE(scenario.journal.read().intent_units == 10);
   if (send_before_exit) REQUIRE(scenario.send(offer) == TRL193_OK);
   REQUIRE(scenario.sends == (send_before_exit ? 1 : 0));
}

void recover(const std::filesystem::path &path, bool filled)
{
   Scenario scenario(path, true);
   TrendlineOffer193 denied{};
   REQUIRE(scenario.prepare(entry(11), denied) == TRL193_RECONCILE);
   auto observation = scenario.inventory();
   observation.complete = false;
   REQUIRE(scenario.observe(observation) == TRL193_RECONCILE);
   observation = scenario.inventory();
   REQUIRE(scenario.observe(observation) == TRL193_OK);
   REQUIRE(scenario.journal.read().in_flight == TRL193_ENTRY);
   REQUIRE(scenario.journal.read().intent_units == 10 && scenario.journal.read().intent_stop == 11030);
   REQUIRE(scenario.prepare(entry(11), denied) == TRL193_RECONCILE);
   observation = scenario.inventory(0, 0, true);
   observation.resolved_intent++;
   REQUIRE(scenario.observe(observation) == TRL193_RECONCILE);
   REQUIRE(scenario.observe(scenario.inventory(filled ? 6 : 0, filled ? 4 : 0, true)) == TRL193_OK);
   if (filled) {
      REQUIRE(scenario.journal.read().held == 4 && scenario.journal.read().pending == 6);
      REQUIRE(scenario.prepare(entry(11), denied) == TRL193_POSITION_LIMIT);
   } else {
      REQUIRE(scenario.prepare(entry(), denied) == TRL193_CONSUMED);
      REQUIRE(scenario.prepare(entry(11), denied) == TRL193_OK);
   }
   REQUIRE(scenario.sends == 0);
}

int main(int argc, char **argv)
{
   try {
      REQUIRE(argc == 3);
      const string test = argv[1];
      const std::filesystem::path path = argv[2];
      if (test == "gates") gate_cases(path);
      else if (test == "accounts") account_cases(path);
      else if (test == "partial") partial_cases(path);
      else if (test == "emergency") emergency_cases(path);
      else if (test == "prepare-before") stop_at_intent(path, false);
      else if (test == "prepare-after") stop_at_intent(path, true);
      else if (test == "recover-flat") recover(path, false);
      else if (test == "recover-partial") recover(path, true);
      else throw std::runtime_error("unknown fixture");
      std::cout << test << " passed\n";
   } catch (const std::exception &error) {
      std::cerr << error.what() << '\n';
      return 1;
   }
}
