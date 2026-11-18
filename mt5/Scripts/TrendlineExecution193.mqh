#ifndef FXDL_TRENDLINE_EXECUTION193
#define FXDL_TRENDLINE_EXECUTION193

// Offline order contract. Native submission is closed in this build.
bool TrendlineOrdersAvailable193() {return false;}

enum TrendlineAction193
{
   TRL193_NONE, TRL193_ENTRY, TRL193_TIGHTEN, TRL193_CANCEL, TRL193_EMERGENCY_CLOSE
};

enum TrendlineResult193
{
   TRL193_OK, TRL193_ACCOUNT_UNAVAILABLE, TRL193_ACCOUNT_TYPE,
   TRL193_ACCOUNT_CHANGED, TRL193_RECONCILE, TRL193_INVENTORY,
   TRL193_POSITION_LIMIT, TRL193_CONSUMED, TRL193_ENTRY_GATE,
   TRL193_PROTECTION, TRL193_HALTED, TRL193_INTENT_UNVERIFIED
};

struct TrendlineAccount193
{
   bool query_ok, connected, tester;
   long mode, login;
   string server;
};

// Independent of account identity. Volumes are exact lot-step units and
// stops are positive tick indices on the same instrument's price grid.
struct TrendlineState193
{
   long revision, last_observation, last_setup, intent_revision;
   long capacity, pending, held, required_stop, intent_units, intent_stop;
   int side;
   TrendlineAction193 in_flight;
   bool halted;
};

struct TrendlineSession193
{
   TrendlineAccount193 connected_account;
   long reconciled_revision;
};

struct TrendlineInventory193
{
   long sequence, pending, held, resolved_intent;
   long pending_stop, position_stop, protected_units;
   int side;
   bool complete, owned;
};

struct TrendlineRequest193
{
   TrendlineAction193 action;
   long setup, units, stop, approved_units;
   int side;
   bool level_q, qualified, entry_paused;
};

// Ephemeral and single use. Only the prepared state is written to storage.
struct TrendlineOffer193
{
   TrendlineState193 prepared;
   bool unused;
};

void InitTrendline193(TrendlineState193 &state)
{
   state.revision=0;state.last_observation=0;state.last_setup=0;state.intent_revision=0;
   state.capacity=0;state.pending=0;state.held=0;state.required_stop=0;
   state.intent_units=0;state.intent_stop=0;
   state.side=0;state.in_flight=TRL193_NONE;state.halted=false;
}

TrendlineResult193 AccountGuard193(const TrendlineAccount193 &account)
{
   if(!account.query_ok || !account.connected || account.tester)
      return TRL193_ACCOUNT_UNAVAILABLE;
   if(account.mode!=ACCOUNT_TRADE_MODE_DEMO) return TRL193_ACCOUNT_TYPE;
   if(account.login<=0 || account.server=="") return TRL193_ACCOUNT_UNAVAILABLE;
   return TRL193_OK;
}

TrendlineResult193 CheckAccount193(const TrendlineSession193 &session,const TrendlineAccount193 &account)
{
   TrendlineResult193 result=AccountGuard193(account);
   if(result!=TRL193_OK) return result;
   result=AccountGuard193(session.connected_account);
   if(result!=TRL193_OK) return result;
   if(account.login!=session.connected_account.login || account.server!=session.connected_account.server)
      return TRL193_ACCOUNT_CHANGED;
   return TRL193_OK;
}

TrendlineResult193 StartTrendline193(TrendlineSession193 &session,const TrendlineAccount193 &account)
{
   session.connected_account=account;
   session.reconciled_revision=-1;
   return AccountGuard193(account);
}

bool ValidTrendlineState193(const TrendlineState193 &state)
{
   if(state.revision<0 || state.revision>=9223372036854775807 || state.last_observation<0 ||
      state.last_setup<0 || state.capacity<0 || state.held<0 || state.held>state.capacity ||
      state.pending<0 || state.pending>state.capacity-state.held ||
      state.in_flight<TRL193_NONE || state.in_flight>TRL193_EMERGENCY_CLOSE)
      return false;
   if(state.in_flight==TRL193_NONE)
   {
      if(state.intent_revision!=0 || state.intent_units!=0 || state.intent_stop!=0) return false;
   }
   else if(state.intent_revision<=0 || state.intent_revision>state.revision ||
           state.intent_units<=0 || state.intent_units>state.capacity) return false;
   if(state.capacity==0)
      return state.in_flight==TRL193_NONE && state.side==0 && state.required_stop==0;
   if(state.last_setup<=0 || (state.side!=1 && state.side!=-1) || state.required_stop<=0)
      return false;
   if(state.in_flight==TRL193_NONE && state.held==0 && state.pending==0) return false;
   if(state.in_flight==TRL193_ENTRY)
      return state.intent_units==state.capacity && state.intent_stop==state.required_stop;
   if(state.in_flight==TRL193_TIGHTEN)
      return state.pending==0 && state.held>0 && state.intent_stop>0 &&
             (state.side==1?state.intent_stop>state.required_stop:state.intent_stop<state.required_stop);
   return state.intent_stop==0;
}

bool AtLeastAsProtective193(const int side,const long observed,const long required)
{
   return observed>0 && (side==1?observed>=required:observed<=required);
}

bool SameTrendlineState193(const TrendlineState193 &a,const TrendlineState193 &b)
{
   return a.revision==b.revision && a.last_observation==b.last_observation && a.last_setup==b.last_setup &&
          a.intent_revision==b.intent_revision &&
          a.capacity==b.capacity && a.pending==b.pending && a.held==b.held && a.required_stop==b.required_stop &&
          a.intent_units==b.intent_units && a.intent_stop==b.intent_stop &&
          a.side==b.side && a.in_flight==b.in_flight && a.halted==b.halted;
}

// Rebuild the state from an authoritative owned inventory observation. The
// caller retains any prepared action until ownership and its outcome reconcile.
TrendlineResult193 ReconcileTrendline193(const TrendlineState193 &saved,TrendlineSession193 &session,
   const TrendlineAccount193 &account,const TrendlineInventory193 &inventory,TrendlineState193 &next)
{
   session.reconciled_revision=-1;
   const TrendlineResult193 guard=CheckAccount193(session,account);
   if(guard!=TRL193_OK) return guard;
   if(!ValidTrendlineState193(saved) || !inventory.complete || inventory.sequence<=saved.last_observation)
      return TRL193_RECONCILE;
   if(inventory.resolved_intent!=0 && inventory.resolved_intent!=saved.intent_revision)
      return TRL193_RECONCILE;
   if(!inventory.owned || inventory.held<0 || inventory.held>saved.capacity || inventory.pending<0 ||
      inventory.pending>saved.capacity-inventory.held || inventory.protected_units<0 ||
      inventory.protected_units>inventory.held ||
      inventory.side!=((inventory.held==0 && inventory.pending==0)?0:saved.side))
      return TRL193_INVENTORY;
   next=saved;
   next.revision++;
   next.last_observation=inventory.sequence;
   next.pending=inventory.pending;
   next.held=inventory.held;
   const bool held_protected=inventory.held==0 || (inventory.protected_units==inventory.held &&
      AtLeastAsProtective193(saved.side,inventory.position_stop,saved.required_stop));
   const bool pending_protected=inventory.pending==0 ||
      AtLeastAsProtective193(saved.side,inventory.pending_stop,saved.required_stop);
   if(!held_protected || !pending_protected) next.halted=true;

   if(saved.in_flight==TRL193_NONE || inventory.resolved_intent!=0)
   {
      next.in_flight=TRL193_NONE;
      next.intent_revision=0;
      next.intent_units=0;next.intent_stop=0;
      if(next.pending==0 && next.held==0)
      {
         next.capacity=0;next.side=0;next.required_stop=0;
      }
      else if(next.pending==0 && held_protected)
         next.required_stop=inventory.position_stop;
      session.reconciled_revision=next.revision;
   }
   else if(saved.in_flight==TRL193_TIGHTEN && (next.held==0 || next.pending!=0))
   {
      // The observation cannot establish which action changed the inventory.
      next=saved;
      return TRL193_RECONCILE;
   }
   return TRL193_OK;
}

TrendlineResult193 PrepareTrendline193(const TrendlineState193 &saved,const TrendlineSession193 &session,
   const TrendlineAccount193 &account,const TrendlineRequest193 &request,TrendlineOffer193 &offer)
{
   offer.unused=false;
   const TrendlineResult193 guard=CheckAccount193(session,account);
   if(guard!=TRL193_OK) return guard;
   if(!ValidTrendlineState193(saved) || session.reconciled_revision!=saved.revision || saved.in_flight!=TRL193_NONE)
      return TRL193_RECONCILE;

   TrendlineState193 prepared=saved;
   long units=0,stop=0;
   switch(request.action)
   {
      case TRL193_ENTRY:
         if(saved.halted) return TRL193_HALTED;
         if(saved.capacity!=0) return TRL193_POSITION_LIMIT;
         if(request.setup<=saved.last_setup) return TRL193_CONSUMED;
         if(!request.level_q || !request.qualified || request.entry_paused ||
            request.units<=0 || request.units>request.approved_units || request.stop<=0 ||
            (request.side!=1 && request.side!=-1)) return TRL193_ENTRY_GATE;
         prepared.last_setup=request.setup;prepared.capacity=request.units;
         prepared.required_stop=request.stop;prepared.side=request.side;
         units=request.units;stop=request.stop;
         break;
      case TRL193_TIGHTEN:
         if(saved.halted) return TRL193_HALTED;
         if(saved.held==0 || saved.pending!=0 || request.stop==saved.required_stop ||
            !AtLeastAsProtective193(saved.side,request.stop,saved.required_stop)) return TRL193_PROTECTION;
         units=saved.held;stop=request.stop;
         break;
      case TRL193_CANCEL:
         if(saved.pending==0) return TRL193_INVENTORY;
         units=saved.pending;
         break;
      case TRL193_EMERGENCY_CLOSE:
         if(!saved.halted || saved.pending!=0 || saved.held==0) return TRL193_PROTECTION;
         units=saved.held;
         break;
      default: return TRL193_ENTRY_GATE;
   }
   prepared.in_flight=request.action;
   prepared.revision++;
   prepared.intent_revision=prepared.revision;
   prepared.intent_units=units;prepared.intent_stop=stop;
   offer.prepared=prepared;offer.unused=true;
   return TRL193_OK;
}

// The fault harness calls this with the durably read back state and a fresh
// account observation. A reconstructed session has no outstanding offer.
TrendlineResult193 TakeSimulatedOffer193(TrendlineOffer193 &offer,const TrendlineState193 &durable,
   TrendlineSession193 &session,const TrendlineAccount193 &fresh_account)
{
   if(!offer.unused) return TRL193_INTENT_UNVERIFIED;
   offer.unused=false;
   const long checked_revision=session.reconciled_revision;
   session.reconciled_revision=-1;
   const TrendlineResult193 guard=CheckAccount193(session,fresh_account);
   if(guard!=TRL193_OK) return guard;
   if(!ValidTrendlineState193(durable) || durable.in_flight==TRL193_NONE ||
      checked_revision!=durable.revision-1 || !SameTrendlineState193(durable,offer.prepared))
      return TRL193_INTENT_UNVERIFIED;
   return TRL193_OK;
}

#endif
