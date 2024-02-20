import xml.etree.ElementTree as ET
import re
from random import randrange,sample,choice

class Muop:

    def __init__(self,name,ports,deps=[]):
        self.name = name
        self.ports = ports
        self.port = None
        self.deps = deps
        self.timestamp = None
        self.flag = False

    def clone(self,deps=None):
        if deps == None:
            deps = self.deps
        m = Muop(
            name=self.name,
            ports=self.ports,
            deps=deps
        )
        return m

    def to_string(
            self,
            all_ports=True,
            mapped_ports=True,
            timestamp=True,
            decorate=True
    ):

        res = self.name

        if decorate:
            res = f"*{res}*" if self.flag else f" {res} "

        if all_ports or mapped_ports:
            res += "["
        
        if all_ports:
            res += self.ports[0]
            for p in self.ports[1:]:
                res += "|" + p
                
        if mapped_ports and self.port is not None:
            res += " -> " + self.port

        if all_ports or mapped_ports:
            res += "]"
            
        if timestamp and self.timestamp is not None:
            res += f" ({self.timestamp})"

        return res
    
    def __str__(self):
        return self.to_string()

class MuopFactory:

    def build(self,max_deps=0):
        if self.history:
            ndeps = randrange(0,max_deps + 1)
        else:
            ndeps = 0
        deps = [choice(self.history) for i in range(ndeps)]
        muop = choice(self.muops).clone(deps=deps)
        self.history.append(muop)
        return muop

class MuopToyFactory(MuopFactory):
    def __init__(self,ports,max_ports_per_op,num_different_ops):
        assert(max_ports_per_op > 1 and len(ports) >= max_ports_per_op)
        self.ports = ports
        self.max_ports_per_op = max_ports_per_op
        self.muops = [Muop(name=f"u{i}",ports=self.dice())
                      for i in range(num_different_ops)]
        self.history = []

    def dice(self):
        nports = randrange(1,self.max_ports_per_op + 1)
        disjunction = sample(self.ports,nports)
        return disjunction

class MuopFileFactory(MuopFactory):
    def __init__(self,filename):

        self.ports = []
        self.muops = []
        self.history = []
        
        root = ET.parse(filename)

        for instrNode in root.iter('instruction'):

            if instrNode.attrib['extension'] != 'BASE':
                continue
            
            name = instrNode.attrib['asm']
            archiNodes = [x for x in instrNode.iter('architecture')
                          if x.attrib['name'] in ['SKL']]
            measuNodes = []
            if archiNodes:
                archiNode = archiNodes[0]
                measuNodes = [x for x in archiNode.iter('measurement')
                              if int(x.attrib['uops']) == 1]
            # if measuNodes:
            if (
                    measuNodes
                    and "load" not in name
                    and "store" not in name
                    and "disp32" not in name
                    and "LEA" not in name
            ):
                measuNode = measuNodes[0]
                match = re.search(r'p([0-9]+)', measuNode.attrib['ports'])
                mports = [f"p{p}" for p in list(match.group(1))]
                self.muops.append(Muop(name=name,ports=mports))
                for p in mports:
                    if p not in self.ports:
                        self.ports.append(p)
