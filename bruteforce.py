from cpu import Backend, ROB, CPU, MuopFactory, Renamer

# Input parameters
ports = ["r0","r1","r2","r3"]
max_ports_per_op = 2
stream_size = 8
# Architectural parameters
rob_size = 3
default_throughput = 1.0
# Execution parameters
niters=100
stop_after_results = 10

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
        flag = cpu.simulate(
            stream,
            iterations=niters,
            search_all=False,
            find_everywhere=False,
            stop_if_flag=False
        )
        
        if cpu.found:

            nom_str_of_stream = cpu.rob.str_of_history(length=len(stream))
            nom_str_of_report = cpu.backend.report()
            m = cpu.rob.tail()
            
            # stream2 = [m.clone() for m in cpu.rob.history[:len(stream)]]
            stream2 = [m.clone() for m in stream]
            backend.accelerate(m.port)
            cpu.simulate(stream2,iterations=niters)
            backend.slowdown(m.port)
            
            # acc_str_of_history = cpu.rob.str_of_history()
            m2 = cpu.rob.tail()

            if m.timestamp == m2.timestamp:
                nresults += 1
                print("Report\n")
                print(f"{nom_str_of_stream}")
                # print(f"> {nom_short_str_of_history}")
                print(f"{nom_str_of_report}")
                # print(f"Acc.: {acc_str_of_history}")
                print()

__main__()
