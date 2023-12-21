from cpu import Backend, ROB, CPU, MuopFactory, Renamer

# Input parameters
ports = ["p0","p1","p2"]
max_ports_per_op = 2
stream_size = 8
# Architectural parameters
rob_size = 3
default_throughput = 1.0
# Execution parameters
niters=1000
# Search parameters
stop_after_results = 10
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
            max_ports_per_op=max_ports_per_op
        )
        
        stream = [factory.build() for x in range(stream_size)]
        cpu.simulate(
            stream,
            iterations=niters,
            search=True,
            search_many=search_many,
            search_unrolled=search_unrolled
        )
        
        if cpu.found:

            nom_str_of_stream = cpu.rob.str_of_history(length=len(stream))
            nom_str_of_report = cpu.backend.report()
            lts = cpu.backend.last_ts

            # Verification: we dump it if m.port (on which stalling occured)
            # is bottleneck
            m = cpu.found[0]
            cpu.simulate_sensitive(
                stream=[oop.clone() for oop in stream],
                port=m.port,
                iterations=niters,
                search=False
            )
            lts2 = cpu.backend.last_ts

            if lts == lts2:

                print("Report\n")
                print(f"Total of {cpu.backend.last_ts} cycles\n")
                print(f"{nom_str_of_stream}")
                print(f"{nom_str_of_report}")
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
                    lts_sens = '%.2f' % (((lts - lts3)/lts)*100)
                    print(f"{p}: {lts_sens}%")

                print()
                
                nresults += 1

__main__()
