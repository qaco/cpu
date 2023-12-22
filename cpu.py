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

    def __init__(self,ports,max_ports_per_op,num_different_ops):
        assert(max_ports_per_op > 1 and len(ports) >= max_ports_per_op)
        self.ports = ports
        self.max_ports_per_op = max_ports_per_op
        self.num_different_ops = num_different_ops
        self.muops = [Muop(name=f"u{i}",ports=self.dice())
                      for i in range(self.num_different_ops)]
        self.history = []

    def dice(self):
        nports = randrange(1,self.max_ports_per_op + 1)
        disjunction = sample(self.ports,nports)
        return disjunction

    def build(self,max_deps=0):
        if self.history:
            ndeps = randrange(0,max_deps + 1)
        else:
            ndeps = 0
        deps = [choice(self.history) for i in range(ndeps)]
        muop = choice(self.muops).clone(deps=deps)
        self.history.append(muop)
        return muop

class Renamer:

    def randomly_map(self,nop):
        nop.port = choice(nop.ports)

    def map(self,nop,backend):
        slots = {}
        for p in nop.ports:
            slots[p] = backend.first_slot_free(p)
        free_port = min(slots, key=slots.get)
        nop.port = free_port
        
class Backend:

    def __init__(self, ports, default_throughput=1.0):
        self.throughputs = {}
        for c in ports:
            self.throughputs[c] = default_throughput

    def clear(self):
        self.last_ts = 0.0
        self.prev_ts = {}
        self.card_ports = {}
        self.stalls = {}
        self.stalling = {}
        for c in self.throughputs:
            self.card_ports[c] = 0
            self.stalls[c] = 0
            self.stalling[c] = False

    def accelerate(self,r):
        assert(r in self.throughputs)
        self.throughputs[r] = self.throughputs[r]/2

    def slowdown(self,r):
        assert(r in self.throughputs)
        self.throughputs[r] = self.throughputs[r]*2
        
    def issue(self,nop):
        if nop.timestamp > 0.0:
            prec = self.prev_ts[nop.port] if nop.port in self.prev_ts else 0.0
            stall = nop.timestamp - prec - self.throughputs[nop.port]
            self.stalling[nop.port] = stall > 0.0
            self.stalls[nop.port] += stall
        self.prev_ts[nop.port] = nop.timestamp
        if nop.timestamp >= self.last_ts:
            self.last_ts = nop.timestamp + self.throughputs[nop.port]
        self.card_ports[nop.port] += 1

    def is_majority(self,port):
        bound = self.card_ports[port]
        for (r,n) in self.card_ports.items():
            if n > bound:
                return False
        return True
            
    def first_slot_free(self,port):
        if port in self.prev_ts:
            slot = (self.prev_ts[port]
                    + self.throughputs[port])
        else:
            slot = 0
        return slot

    def saturation(self,port):
        pstalls = self.stalls[port]
        sat = 100 - (pstalls/self.last_ts)*100 if self.last_ts else 0.0
        return sat
    
    def report(self,vertical=True):
        sep = "\n" if vertical else "  "
        rep = ""
        for p in self.stalls:
            sat = '%.2f' % self.saturation(p)
            pstalls = str(self.stalls[p])
            rep += f"{p}:{sat}% ({pstalls} stalls)" + sep
        return rep

    def __str__(self):
        return self.report()
    
class ROB:

    def __init__(self,size=4):
        self.size = size
        self.clear()

    def clear(self):
        self.history = []
        self.buff = []

    def full(self):
        return len(self.buff) == self.size

    def empty(self):
        return len(self.buff) == 0

    def tail(self):
        assert(len(self.buff))
        return self.buff[-1]

    def head(self):
        assert(len(self.buff))
        return self.buff[0]

    def rotate(self):
        assert(not self.empty())
        self.buff = self.buff[1:]

    def insert(self,nop):
        assert(len(self.buff) < self.size)
        self.buff.append(nop)
        self.history.append(nop)

    def str_of_history(self,vertical=True,length=-1):
        sep = "\n" if vertical else " // "
        res = ""
        for i,m in enumerate(self.history):
            res += str(m) + sep
            if i+1 == length:
                break
        return res
    
class CPU:

    def __init__(self,renamer,backend,rob):
        self.renamer = renamer
        self.backend = backend
        self.rob = rob
        self.clear()
    
    def clear(self):
        self.found = []
        self.rob.clear()
        self.backend.clear()

    # Algo

    def simulate_sensitive(
            self,
            stream,
            port,
            iterations=1,
            search=False,
            search_many=False,
            search_unrolled=False,
    ):
        self.backend.accelerate(port)
        self.simulate(
            stream=stream,
            iterations=iterations,
            search=search,
            search_many=search_many,
            search_unrolled=search_unrolled
        )
        self.backend.slowdown(port)
    
    def simulate(
            self,
            stream,
            iterations=1,
            search=False,
            search_many=False,
            search_unrolled=False,
    ):

        self.clear()
        
        offset = 0
        
        counter = 0
        for i in range(0,iterations):
            for nop in stream:
                nop = nop.clone()
                # Retire the oldest muop
                if self.rob.full():
                    oop = self.rob.head()
                    noffset = (oop.timestamp
                               + self.backend.throughputs[oop.port])
                    offset = max(noffset,offset)
                    self.rob.rotate()
                # Insert a new muop
                self.renamer.map(nop,self.backend)
                self.rob.insert(nop)
                nop.timestamp = max(self.backend.first_slot_free(nop.port),
                                    offset)
                self.backend.issue(nop)
                # Out if stop conditions are met
                if (
                        search and
                        (search_many or len(self.found) == 0) and
                        (search_unrolled or counter < len(stream)) and
                        self.is_muop_of_interest(nop)
                ):
                    self.found.append(nop)
                    nop.flag = True
                    
                counter += 1

    def is_muop_of_interest(self,nop):
        return (
            self.backend.stalling[nop.port] and
            self.backend.is_majority(nop.port)
        )
