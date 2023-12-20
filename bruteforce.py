from cpu import Backend, ROB, CPU, MuopFactory

def __main__():

    # Params
    
    ports = ["r0","r1","r2","r3"]
    rob_size = 3
    stream_size = 8
    default_throughput = 1.0

    # Construction
    
    backend = Backend(
        ports=ports,
        default_throughput=default_throughput
    )
    rob = ROB(size=rob_size)
    cpu = CPU(backend=backend,rob=rob)

    # Computation
    
    while True:

        factory = MuopFactory(ports=ports)
        
        stream = [factory.random() for x in range(stream_size)]
        found = cpu.simulate(stream, stop_if_flag=True)
        
        if found:

            nom_str_of_history = cpu.rob.str_of_history()
            m = cpu.rob.tail()
            
            stream2 = [m.clone() for m in cpu.rob.history]
            backend.accelerate(m.port)
            cpu.simulate(stream2,stop_if_flag=False)
            backend.slowdown(m.port)
            
            acc_str_of_history = cpu.rob.str_of_history()
            m2 = cpu.rob.tail()

            if m.timestamp == m2.timestamp:
                print(f"Nom.: {nom_str_of_history}")
                print(f"Acc.: {acc_str_of_history}\n")

__main__()
