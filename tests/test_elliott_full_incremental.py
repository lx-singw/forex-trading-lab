"""Every-prefix equivalence to the retained batch detector and fork isolation."""
import random
import unittest
from forex_demo_lab.elliott_full.contracts import Bar,D
from forex_demo_lab.elliott_full.patterns import confirmed
from forex_demo_lab.elliott_full.incremental import ConfirmedPivots
from forex_demo_lab.elliott_full.strategy import Strategy


def bar(i,price,high=None,low=None):
    price=D(price)
    return Bar("H1",i*3600000,(i+1)*3600000,(i+1)*3600000+2000+i,
               price,D(high) if high is not None else price+D(".0001"),
               D(low) if low is not None else price-D(".0001"),price,str(i))


class IncrementalTests(unittest.TestCase):
    def test_every_prefix_matches_batch_for_all_radii_ties_and_replacements(self):
        rng=random.Random(144)
        histories=[[],[]]
        for i in range(300):
            center=D("1.1")+D(rng.randrange(-10,11))/10000
            histories[0].append(bar(i,center,center+D(rng.randrange(0,5))/10000,center-D(rng.randrange(0,5))/10000))
            histories[1].append(bar(i,D("2.2")-center))
        for history in histories:
            for radius in (2,4,8):
                stream=ConfirmedPivots(radius)
                for n in range(1,len(history)+1):
                    stream.append(history[:n])
                    journal,chain=confirmed(history[:n],radius)
                    self.assertEqual(journal,stream.journal,(radius,n))
                    self.assertEqual(chain,stream.chain,(radius,n))

    def test_no_early_pivot_and_confirmation_uses_right_bar_publication(self):
        rows=[bar(i,str(v)) for i,v in enumerate((1,2,3,2,1,2,3))]
        stream=ConfirmedPivots(2)
        for n in range(1,5):
            stream.append(rows[:n]);self.assertFalse(stream.journal)
        stream.append(rows[:5]);point=stream.journal[0]
        self.assertEqual(2,point.index)
        self.assertEqual(rows[4].available,point.available)
        for n in (6,7):stream.append(rows[:n])
        self.assertEqual(point,stream.journal[0])

    def test_fork_and_bootstrap_do_not_mutate_prior_published_pivots(self):
        rows=[bar(i,str(v)) for i,v in enumerate((1,2,3,2,1,2,4,2,1))]
        stream=ConfirmedPivots.bootstrap(rows[:5],2);fork=stream.fork()
        before=list(stream.journal);chain=list(stream.chain)
        for n in range(6,len(rows)+1):fork.append(rows[:n])
        self.assertEqual(before,stream.journal);self.assertEqual(chain,stream.chain)
        self.assertEqual(confirmed(rows,2),(fork.journal,fork.chain))
        with self.assertRaises(ValueError):fork.append(rows)
        for radius in (True,1,0,3):
            with self.assertRaises(ValueError):ConfirmedPivots(radius)

    def test_strategy_fork_caches_are_isolated(self):
        rows=[bar(i,str(v)) for i,v in enumerate((1,2,3,2,1,2,4,2,1))]
        strategy=Strategy()
        for row in rows[:5]:strategy.on_bar(row)
        before=list(strategy.pivot_streams['H1'][2].journal)
        fork=strategy.fork()
        for row in rows[5:]:fork.on_bar(row)
        self.assertEqual(before,strategy.pivot_streams['H1'][2].journal)
        self.assertEqual(confirmed(rows,2)[0],fork.pivot_streams['H1'][2].journal)


if __name__=="__main__":unittest.main()
