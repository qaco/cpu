from cpu import Backend, ROB, CPU, Renamer
from muop import Muop

# Architectural parameters
rob_size = 4
default_throughput = 1.0
# Execution parameters
niters=1000
# Search parameters
search=True
search_many=False
search_unrolled= False

skylake_ports = ["p0","p6","p1","p5","p2","p3"]

stream = [
        Muop(name="ADD",ports=["p0","p1","p5","p6"]),
        Muop(name="SHL",ports=["p0","p6"]),
        Muop(name="BTS",ports=["p0","p6"]),
        Muop(name="CMOVNLE",ports=["p0","p6"]),
        Muop(name="ADD",ports=["p0","p1","p5","p6"]),
        Muop(name="XOR",ports=["p0","p1","p5","p6"]),
        Muop(name="BSF",ports=["p1"]),
        Muop(name="LAHF",ports=["p0","p6"]),
        Muop(name="MUL",ports=["p1"]),
        Muop(name="ADD",ports=["p0","p1","p5","p6"]),
        Muop(name="AND",ports=["p0","p1","p5","p6"]),
        Muop(name="CMOVB",ports=["p0","p6"]),
]

def __main__():

    # Construction

    backend = Backend(
        ports=skylake_ports,
        default_throughput=default_throughput
    )
    renamer = Renamer()
    rob = ROB(size=rob_size)
    cpu = CPU(backend=backend,rob=rob,renamer=renamer)

    # Computation
    
    cpu.simulate(
        stream,
        iterations=niters,
        search=search,
        search_many=search_many,
        search_unrolled=search_unrolled
    )

    # cpu.simulate_sensitive(
    #     stream,
    #     port="p0",
    #     iterations=niters,
    #     search=search,
    #     search_many=search_many,
    #     search_unrolled=search_unrolled
    # )
        
    nominal_sats = {}
    for p in skylake_ports:
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
    str_of_history = cpu.rob.str_of_history(length=len(stream)*2)
    str_of_saturation = str(cpu.backend)

            # Verification: we dump it if m.port (on which stalling occured)
            # is bottleneck
    lts = cpu.backend.last_ts
            
    str_of_sens = ""
    for p in skylake_ports:
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

    print(f"===\nProgram: {str_of_stream}\n")
    print(f"For {niters} iterations: {lts} cycles\n")
    print(f"Portmapping & timing\n{str_of_history}...\n")
    print(f"Saturation\n{str_of_saturation}")
    print(f"Sensitivity\n{str_of_sens}")

__main__()
