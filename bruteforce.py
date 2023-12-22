from cpu import Backend, ROB, CPU, MuopFactory, Renamer

# Architectural parameters
rob_size = 3
default_throughput = 1.0
ports = ["p0","p1","p2"]
# Muops parameters
max_ports_per_op = 2
num_different_ops = 5
stream_size = 8
# Execution parameters
niters=1000
# Search parameters
stop_after_results = 10
search=True
search_many=False
search_unrolled= False

# Checks
assert(len(ports) > 0)
assert(max_ports_per_op > 0)
assert(len(ports) > max_ports_per_op)


def __main__():

    # Construction

    backend = Backend(
        ports=ports,
        default_throughput=default_throughput
    )
    renamer = Renamer()
    rob = ROB(size=rob_size)
    cpu = CPU(backend=backend,rob=rob,renamer=renamer)

    # Computation

    nresults = 0
    while nresults < stop_after_results:

        factory = MuopFactory(
            ports=ports,
            max_ports_per_op=max_ports_per_op,
            num_different_ops=num_different_ops
        )
        
        stream = [factory.build() for x in range(stream_size)]
        cpu.simulate(
            stream,
            iterations=niters,
            search=search,
            search_many=search_many,
            search_unrolled=search_unrolled
        )
        
        if cpu.found:

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
            
            print(f"===\nProgram: {str_of_stream}\n")
            print(f"For {niters} iterations: {cpu.backend.last_ts} cycles\n")
            print(f"Portmapping & timing\n{str_of_history}...\n")
            print(f"Saturation\n{str_of_saturation}")
            
            print("Sensitivity")
                
            for p in ports:
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
                speedup_percent = '%.2f' % ((speedup/lts)*100)
                print(f"{p}: {speedup_percent}% ({speedup} cycles)")

            print()
                
            nresults += 1

__main__()
