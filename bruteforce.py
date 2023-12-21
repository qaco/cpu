from cpu import Backend, ROB, CPU, MuopFactory, Renamer

def __main__():

    # Params
    
    ports = ["r0","r1","r2","r3"]
    rob_size = 3
    stream_size = 8
    niters=1
    default_throughput = 1.0
    max_ports_per_op = 2

    # Construction

    backend = Backend(
        ports=ports,
        default_throughput=default_throughput
    )
    renamer = Renamer()
    rob = ROB(size=rob_size)
    cpu = CPU(backend=backend,rob=rob,renamer=renamer)

    # Computation
    
    while True:

        factory = MuopFactory(
            ports=ports,
            max_ports_per_op=max_ports_per_op
        )
        
        stream = [factory.build() for x in range(stream_size)]
        found = cpu.simulate(stream,iterations=niters,stop_if_flag=True)
        
        if found:

            nom_str_of_history = cpu.rob.str_of_history()
            m = cpu.rob.tail()
            
            stream2 = [m.clone() for m in cpu.rob.history]
            backend.accelerate(m.port)
            cpu.simulate(stream2,iterations=niters,stop_if_flag=False)
            backend.slowdown(m.port)
            
            acc_str_of_history = cpu.rob.str_of_history()
            m2 = cpu.rob.tail()

            if m.timestamp == m2.timestamp:
                print(f"Nom.: {nom_str_of_history}")
                print(f"Acc.: {acc_str_of_history}\n")

__main__()
