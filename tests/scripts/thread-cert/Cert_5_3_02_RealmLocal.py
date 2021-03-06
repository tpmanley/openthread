#!/usr/bin/env python3
#
#  Copyright (c) 2016, The OpenThread Authors.
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#  3. Neither the name of the copyright holder nor the
#     names of its contributors may be used to endorse or promote products
#     derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#

import unittest

import node
import config

LEADER = 1
ROUTER1 = 2
DUT_ROUTER2 = 3
SED1 = 4


class Cert_5_3_2_RealmLocal(unittest.TestCase):
    def setUp(self):
        self.simulator = config.create_default_simulator()

        self.nodes = {}
        for i in range(1, 5):
            self.nodes[i] = node.Node(i, (i == SED1), simulator=self.simulator)

        self.nodes[LEADER].set_panid(0xface)
        self.nodes[LEADER].set_mode('rsdn')
        self.nodes[LEADER].add_whitelist(self.nodes[ROUTER1].get_addr64())
        self.nodes[LEADER].enable_whitelist()

        self.nodes[ROUTER1].set_panid(0xface)
        self.nodes[ROUTER1].set_mode('rsdn')
        self.nodes[ROUTER1].add_whitelist(self.nodes[LEADER].get_addr64())
        self.nodes[ROUTER1].add_whitelist(self.nodes[DUT_ROUTER2].get_addr64())
        self.nodes[ROUTER1].enable_whitelist()
        self.nodes[ROUTER1].set_router_selection_jitter(1)

        self.nodes[DUT_ROUTER2].set_panid(0xface)
        self.nodes[DUT_ROUTER2].set_mode('rsdn')
        self.nodes[DUT_ROUTER2].add_whitelist(self.nodes[ROUTER1].get_addr64())
        self.nodes[DUT_ROUTER2].add_whitelist(self.nodes[SED1].get_addr64())
        self.nodes[DUT_ROUTER2].enable_whitelist()
        self.nodes[DUT_ROUTER2].set_router_selection_jitter(1)

        self.nodes[SED1].set_panid(0xface)
        self.nodes[SED1].set_mode('sn')
        self.nodes[SED1].add_whitelist(self.nodes[DUT_ROUTER2].get_addr64())
        self.nodes[SED1].enable_whitelist()
        self.nodes[SED1].set_timeout(config.DEFAULT_CHILD_TIMEOUT)

    def tearDown(self):
        for n in list(self.nodes.values()):
            n.stop()
            n.destroy()
        self.simulator.stop()

    def test(self):
        # 1
        self.nodes[LEADER].start()
        self.simulator.go(5)
        self.assertEqual(self.nodes[LEADER].get_state(), 'leader')

        self.nodes[ROUTER1].start()
        self.simulator.go(5)
        self.assertEqual(self.nodes[ROUTER1].get_state(), 'router')

        self.nodes[DUT_ROUTER2].start()
        self.simulator.go(5)
        self.assertEqual(self.nodes[DUT_ROUTER2].get_state(), 'router')

        self.nodes[SED1].start()
        self.simulator.go(5)
        self.assertEqual(self.nodes[SED1].get_state(), 'child')

        # 2 & 3
        mleid = self.nodes[DUT_ROUTER2].get_ip6_address(
            config.ADDRESS_TYPE.ML_EID
        )
        self.assertTrue(self.nodes[LEADER].ping(mleid, size=256))
        self.assertTrue(self.nodes[LEADER].ping(mleid))

        # 4 & 5
        self.assertTrue(
            self.nodes[LEADER].ping('ff03::1', num_responses=2, size=256)
        )
        sed_messages = self.simulator.get_messages_sent_by(SED1)
        self.assertFalse(sed_messages.contains_icmp_message())

        self.assertTrue(self.nodes[LEADER].ping('ff03::1', num_responses=2))
        sed_messages = self.simulator.get_messages_sent_by(SED1)
        self.assertFalse(sed_messages.contains_icmp_message())

        # 6 & 7
        self.assertTrue(
            self.nodes[LEADER].ping('ff03::2', num_responses=2, size=256)
        )
        sed_messages = self.simulator.get_messages_sent_by(SED1)
        self.assertFalse(sed_messages.contains_icmp_message())

        self.assertTrue(self.nodes[LEADER].ping('ff03::2', num_responses=2))
        sed_messages = self.simulator.get_messages_sent_by(SED1)
        self.assertFalse(sed_messages.contains_icmp_message())

        # 8
        self.assertTrue(
            self.nodes[LEADER].ping(
                config.REALM_LOCAL_All_THREAD_NODES_MULTICAST_ADDRESS,
                num_responses=3,
                size=256,
            )
        )
        self.simulator.go(2)
        sed_messages = self.simulator.get_messages_sent_by(SED1)
        self.assertTrue(sed_messages.contains_icmp_message())

        self.assertTrue(
            self.nodes[LEADER].ping(
                config.REALM_LOCAL_All_THREAD_NODES_MULTICAST_ADDRESS,
                num_responses=3,
            )
        )
        self.simulator.go(2)
        sed_messages = self.simulator.get_messages_sent_by(SED1)
        self.assertTrue(sed_messages.contains_icmp_message())


if __name__ == '__main__':
    unittest.main()
