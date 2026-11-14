"""Separate fixture correction; original frozen084 failure remains evidence."""
import test_synchronization_084 as original
from forex_demo_lab.synchronization_084 import Companion084


class Sync084R2Tests(original.Sync084Tests):
    def test_owned_cleanup_after_date_expiry(self):
        c,b,clock,state=original.fixture084();c.start(True);clock.advance(86400000)
        with self.assertRaises(Exception):c.exchange('ready',clock.boot+60000)
        # Overall validity stays rejected after expiry even when physical model
        # handles receive their closes. The old fixture confused these outcomes.
        self.assertFalse(c.finish());self.assertFalse(b.handles)
        self.assertEqual(b.finish_calls,1);self.assertEqual(c.owner.unconfirmed,0)

    def test_cleanup_return_after_whole_deadline_rejects_but_closes_once(self):
        c,b,clock,state=original.fixture084();c.start(True)
        finish=b.finish
        def late_finish():
            clock.advance(120000)
            return finish()
        b.finish=late_finish
        self.assertFalse(c.finish());self.assertFalse(b.handles)
        self.assertEqual(b.finish_calls,1);self.assertEqual(len(b.closed),len(set(b.closed)))
        with self.assertRaises(Exception):c.finish()
        self.assertEqual(b.finish_calls,1)

    def test_excessive_episode_deadline_rejects_before_transport(self):
        c,b,clock,state=original.fixture084();c.start(True)
        with self.assertRaises(Exception):c.exchange('ready',clock.boot+60001)
        self.assertFalse(b.requests);self.assertFalse(b.publications)
        self.assertTrue(c.finish());self.assertFalse(b.handles)
