'''
Created on May 15, 2018

@author: 4x1md

Update of original file on Nov. 17 2018 by Dundarave to add entries needed for FY6600 support.
'''

from awgdrivers.dummy_awg import DummyAWG
from awgdrivers.psg9080 import PSG9080
from awgdrivers.jds6600 import JDS6600
from awgdrivers.bk4075 import BK4075
from awgdrivers.fy import FygenAWG
from awgdrivers.fy6900 import Fy6900AWG
from awgdrivers.fy6600 import FY6600
from awgdrivers.ad9910 import AD9910
from awgdrivers.dg800 import RigolDG800
from awgdrivers.dg800P import RigolDG800P
from awgdrivers.utg1000x import UTG1000x
from awgdrivers.utg900e import UTG900e
from awgdrivers.sdg1050 import SDG1050
from awgdrivers.hp8116a import HP8116A


class AwgFactory(object):

    def __init__(self):
        self.awgs = {}

    def add_awg(self, short_name, awg_class):
        self.awgs[short_name] = awg_class

    def get_class_by_name(self, short_name):
        return self.awgs[short_name]

    def get_names(self):
        # get the names of the AWGs, sorted alphabetically, but with "dummy" first
        out = []
        for a in self.awgs:
            if a != "dummy":
                out.append(a)
        out = sorted(out)
        out.insert(0, "dummy")
        return out


# Initialize factory
awg_factory = AwgFactory()
drivers = (
    DummyAWG,
    PSG9080,
    JDS6600,
    BK4075,
    FygenAWG,
    Fy6900AWG,
    FY6600,
    AD9910,
    RigolDG800,
    RigolDG800P,
    UTG1000x,
    SDG1050,
    UTG900e,
    HP8116A
)
for driver in drivers:
    awg_factory.add_awg(driver.SHORT_NAME, driver)
