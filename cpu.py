from random import randrange

class Muop:

    def __init__(self,name,port,deps):
        self.name = name
        self.port = port
        self.deps = deps
        self.timestamp = None

    def clone(self):
        m = Muop(
            name=self.name,
            port=self.port,
            deps=self.deps
        )
        return m
        
    def __str__(self):
        res = self.name
        res += f"[{self.port}]"
        if self.timestamp is not None:
            res += f"({self.timestamp})"
        return res

class MuopFactory:

    def __init__(self,ports):
        self.ports = ports
        self.history = []
        self.stamp = 0

    def random(self,max_deps=0):
        assert(self.ports)
        res = self.ports[randrange(0,len(self.ports))]
        
        if self.history:
            ndeps = randrange(0,max_deps + 1)
        else:
            ndeps = 0
        deps = [self.history[randrange(0,len(self.history))]
                for i in range(ndeps)]
        muop = Muop(name=f"u{self.stamp}",port=res,deps=deps)
        self.stamp += 1
        self.history.append(muop)
        return muop

class Backend:

    def __init__(self, ports, default_throughput=1.0):
        self.throughputs = {}
        for c in ports:
            self.throughputs[c] = default_throughput

    def clear(self):
        self.history = []
        self.last_ts = {}
        self.card_ports = {}
        for c in self.throughputs:
            self.card_ports[c] = 0

    def accelerate(self,r):
        assert(r in self.throughputs)
        self.throughputs[r] = self.throughputs[r]/2

    def slowdown(self,r):
        assert(r in self.throughputs)
        self.throughputs[r] = self.throughputs[r]*2
        
    def issue(self,nop):
        self.last_ts[nop.port] = nop.timestamp
        self.card_ports[nop.port] += 1
        self.history.append(nop)

    def is_stalling(self,nop):
        if nop.port in self.last_ts:
            delay = nop.timestamp - self.last_ts[nop.port]
            return delay > self.throughputs[nop.port]
        else:
            False

    def is_majority(self,port):
        bound = self.card_ports[port]
        for (r,n) in self.card_ports.items():
            if n > bound:
                return False
        return True
            
    def first_slot_free(self,nop):
        if nop.port in self.last_ts:
            slot = (self.last_ts[nop.port]
                    + self.throughputs[nop.port])
        else:
            slot = 0
        return slot

    def str_of_history(self):
        res = ""
        for m in self.history:
            res += str(m) + " "
        return res
        
class ROB:

    def __init__(self,size=4):
        self.size = size
        self.clear()

    def clear(self):
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
    
class CPU:

    def __init__(self,backend,rob):
        self.backend = backend
        self.rob = rob
        self.clear()
    
    def clear(self):
        self.rob.clear()
        self.backend.clear()

    # Algo

    def simulate(self,stream,stop_if_flag):

        self.clear()
        
        offset = 0
        flag = False
        
        for nop in stream:
            # Retire the oldest muop
            if self.rob.full():
                oop = self.rob.head()
                noffset = (oop.timestamp
                           + self.backend.throughputs[oop.port])
                offset = max(noffset,offset)
                self.rob.rotate()
            # Insert a new muop
            self.rob.insert(nop)
            nop.timestamp = max(self.backend.first_slot_free(nop),
                                offset)
            # Post-processing (!! the order matters)
            flag = (self.backend.is_stalling(nop) and
                    self.backend.is_majority(nop.port))
            self.backend.issue(nop)
            # Out if stop conditions are met
            if flag and stop_if_flag:
                break

        return flag
