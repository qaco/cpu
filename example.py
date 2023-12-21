from cpu import Backend, ROB, CPU, Muop, Renamer

def __main__():

    # Params
    
    ports = ["p0","p1","p2","p3"]
    rob_size = 3
    niters=10000
    default_throughput = 1.0

    # Construction

    backend = Backend(
        ports=ports,
        default_throughput=default_throughput
    )
    renamer = Renamer()
    rob = ROB(size=rob_size)
    cpu = CPU(backend=backend,rob=rob,renamer=renamer)

    stream = [
        Muop(name="u1",ports=["p0"]),
        Muop(name="u2",ports=["p0"]),
        Muop(name="u3",ports=["p1"]),
        Muop(name="u4",ports=["p1"]),
        Muop(name="u5",ports=["p2"]),
        Muop(name="u6",ports=["p3"]),
        Muop(name="u7",ports=["p2"]),
        Muop(name="u8",ports=["p1"]),
    ]

    cpu.simulate(stream,iterations=niters,stop_if_flag=False)
    nom_str_of_history = cpu.rob.str_of_history(length=len(stream),vertical=True)
    nom_str_of_report = cpu.backend.report()
    print(nom_str_of_history)
    print(nom_str_of_report)
    
__main__()
