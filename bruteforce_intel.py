from cpu import Backend, ROB, CPU, Renamer
from muop import MuopFileFactory

# Architectural parameters
rob_size = 4
default_throughput = 1.0
# Muops parameters
stream_size = 12
# Execution parameters
niters=1000
# Search parameters
search=True
search_many=False
search_unrolled= False
floor_sens=5.0

def __main__():

    # Construction

    factory = MuopFileFactory(filename='instructions.xml')
    
    backend = Backend(
        ports=factory.ports,
        default_throughput=default_throughput
    )
    renamer = Renamer()
    rob = ROB(size=rob_size)
    cpu = CPU(backend=backend,rob=rob,renamer=renamer)

    # Computation

    while True:
        
        stream = [factory.build() for x in range(stream_size)]
        cpu.simulate(
            stream,
            iterations=niters,
            search=search,
            search_many=search_many,
            search_unrolled=search_unrolled
        )
        
        if cpu.found:

            nominal_sats = {}
            for p in factory.ports:
                nominal_sats[p] = cpu.backend.saturation(p)

            strs_of_stream = []
            for mu in stream:
                str_of_mu = mu.to_string(
                    all_ports=False,
                    mapped_ports=False,
                    timestamp=False,
                    decorate=False
                )
                strs_of_stream.append(str_of_mu)
            str_of_stream = " ".join(strs_of_stream)
            str_of_history = cpu.rob.str_of_history(length=len(stream))
            str_of_saturation = str(cpu.backend)

            # Verification: we dump it if m.port (on which stalling occured)
            # is bottleneck
            lts = cpu.backend.last_ts
            m = cpu.found[0]
            cpu.simulate_sensitive(
                stream=[oop.clone() for oop in stream],
                port=m.port,
                iterations=niters,
                search=False
            )
            lts2 = cpu.backend.last_ts
            if lts != lts2:
                continue
            
            
            relevant = False
            str_of_sens = ""
            for p in factory.ports:
                if p == m.port:
                    lts3 = lts2
                else:
                    cpu.simulate_sensitive(
                        stream=[oop.clone() for oop in stream],
                        port=p,
                        iterations=niters,
                        search=False
                    )
                    lts3 = cpu.backend.last_ts
                speedup = lts - lts3
                speedup_percent = (speedup/lts)*100
                speedup_percent_str = '%.2f' % speedup_percent
                sat = nominal_sats[p]
                
                sens= f"{p}: {speedup_percent_str}% ({speedup} cycles)"
                str_of_sens += f"{sens}\n"

                relevant = (
                    relevant
                    or (speedup_percent > floor_sens and sat < 95.0)
                )

            if not relevant:
                continue
            else:
                relevant = False

            print(f"===\nProgram: {str_of_stream}\n")
            print(f"For {niters} iterations: {lts2} cycles\n")
            print(f"Portmapping & timing\n{str_of_history}...\n")
            print(f"Saturation\n{str_of_saturation}")
            print(f"Sensitivity\n{str_of_sens}")

            ncont = "x"
            while (ncont != "y" and ncont != "n" and ncont != ""):
                ncont = input("Continue ? [y/n]")
            if ncont == "n":
                break

__main__()
