from argparse import ArgumentParser, RawTextHelpFormatter
from truncboom import TruncatedBoomerang
from diff import Diff
from plotdistinguisher import *

def main():

    # 13 rounds
    # r0, rm, r1 = 3, 8, 2
    # w0, wDDT, wFBCT, wDDT2, w1 = 6, 1, 2, 4, 6

    # 14 rounds
    # r0, rm, r1 = 4, 7, 3
    # w0, wDDT, wFBCT, wDDT2, w1 = 6, 1, 2, 4, 6

    # 15 rounds
    # r0, rm, r1 = 4, 7, 4
    # w0, wDDT, wFBCT, wDDT2, w1 = 6, 1, 2, 4, 6

    # 16 rounds
    # r0, rm, r1 = 4, 8, 4
    # w0, wDDT, wFBCT, wDDT2, w1 = 6, 1, 2, 4, 6

    parser = ArgumentParser(description="This tool finds the nearly optimum boomerang distinguisher\n"
                                         "Example:\n"
                                         "python3 boom.py -r0 4 -rm 8 -r1 4 -w0 6 -wDDT 1 -wFBCT 2 -wDDT2 4 -w1 6",
                            formatter_class=RawTextHelpFormatter)
                        
    parser.add_argument('-i', '--inputfile', type=str, help="Use an input file in yaml format")
    parser.add_argument('-r0', '--r0', type=int,
                        help="number of rounds covered by E0")
    parser.add_argument('-rm', '--rm', type=int,
                        help="number of rounds covered by Em")
    parser.add_argument('-r1', '--r1', type=int,
                        help="number of rounds covered by E1")
    parser.add_argument('-w0', '--w0', type=int,
                        help="cost of active S-boxes in E0")
    parser.add_argument('-wDDT', '--wDDT', type=int,
                        help="cost of DDT S-boxes in Em")
    parser.add_argument('-wFBCT', '--wFBCT', type=int,
                        help="cost of FBCT S-boxes in Em")
    parser.add_argument('-wDDT2', '--wDDT2', type=int,
                        help="cost of DDT2 S-boxes in Em")
    parser.add_argument('-w1', '--w1', type=int,
                        help="cost of active S-boxes in E1")
    parser.add_argument('-tl', '--timelimit', type=int,
                        help="time limit in seconds")
    parser.add_argument('-ns', '--numofsols', type=int,
                        help="number of solutions (currently disabled)")

    # Parse command line arguments and construct parameter list.
    args = parser.parse_args()
    params = loadparameters(args)
    r0, rm, r1 = params["r0"], params["rm"], params["r1"]
    w0, wDDT, wFBCT, wDDT2, w1 = params["w0"], params["wDDT"], params["wFBCT"], params["wDDT2"], params["w1"]

    assert(rm > 0)
    tex_content = tex_init()
    ##############################################################################################
    ##############################################################################################
    # Step1- Find a truncated boomerang trail
    bm = TruncatedBoomerang(r0=r0, r1=r1, rm=rm, w0=w0, w1=w1, wDDT=wDDT, wFBCT=wFBCT, wDDT2=wDDT2)
    bm.iterative = False
    bm.find_truncated_boomerang_trail()
    upper_trail, middle_part, lower_trail = bm.parse_solver_output()
    ##############################################################################################
    ##############################################################################################
    # Step2- Instantiate the upper/lower truncated trails with real differential trails
    diff_upper_trail = None
    diff_effect_upper = 0
    if r0 != 0:
        time_limit = 18000
        params = {"nrounds" : bm.r0,
                  "mode" : 0,
                  "startweight" : 0,
                  "endweight" : 128,
                  "timelimit" : time_limit,
                  "numberoftrails" : 1,
                  "fixedVariables" : {}}
        for nibble in range(16):
            if upper_trail[f"x_0"][nibble] == "0":
                for bit in range(4):
                    params["fixedVariables"][f"x_{0}_{nibble}_{bit}"] = "0"
            if upper_trail[f"x_{bm.r0}"][nibble] == "0":
                for bit in range(4):
                    params["fixedVariables"][f"x_{bm.r0}_{nibble}_{bit}"] = "0"
        diff = Diff(params)
        diff.make_model()
        diff_upper_trail = diff.solve()
        params["fixedVariables"] = {"x_0": diff_upper_trail["x_0"], f"x_{bm.r0}": diff_upper_trail[f"x_{bm.r0}"]}
        params["mode"] = 2
        diff = Diff(params)
        diff.make_model()
        diff_effect_upper = diff.solve()
    ##############################################################################################
    diff_lower_trail = None
    diff_effect_lower = 0
    if r1 != 0:
        time_limit = 18000
        params = {"nrounds" : bm.r1,
                  "mode" : 0,
                  "startweight" : 0,
                  "endweight" : 128,
                  "timelimit" : time_limit,
                  "numberoftrails" : 1,
                  "fixedVariables" : {}}
        for nibble in range(16):
            if lower_trail[f"x_{bm.rm}"][nibble] == "0":
                for bit in range(4):
                    params["fixedVariables"][f"x_{0}_{nibble}_{bit}"] = "0"
            if lower_trail[f"x_{bm.R1}"][nibble] == "0":
                for bit in range(4):
                    params["fixedVariables"][f"x_{bm.r1}_{nibble}_{bit}"] = "0"
        diff = Diff(params)
        diff.make_model()
        diff_lower_trail = diff.solve()
        params["fixedVariables"] = {"x_0": diff_lower_trail["x_0"], f"x_{bm.r1}": diff_lower_trail[f"x_{bm.r1}"]}
        params["mode"] = 2
        diff = Diff(params)
        diff.make_model()
        diff_effect_lower = diff.solve()
    ##############################################################################################
    ##############################################################################################
    # print out a summary of result on terminal
    print("#"*27)
    print("Summary of the results:")
    print("Upper trail:")
    if diff_upper_trail != None:
        diff.print_trail(diff_trail=diff_upper_trail)
    print("#"*27)
    mactive_sboxes = middle_part["as"]
    print(f"Sandwich {rm} rounds in the middle with {mactive_sboxes} active S-boxes")
    print("#"*27)
    print("Lower trail:")
    if diff_lower_trail != None:
        diff.print_trail(diff_trail=diff_lower_trail)
    print("-"*27)
    total_weight = 0
    if diff_effect_upper != None:
        print("differential effect of the upper trail: 2^(%0.02f)" % diff_effect_upper)
        total_weight += diff_effect_upper*2
    if diff_effect_lower != None:
        print("differential effect of the lower trail: 2^(%0.02f)" % diff_effect_lower)
        total_weight += diff_effect_lower*2
    upper_bound =  total_weight + (-1.8)*mactive_sboxes
    lower_bound = total_weight + (-2)*mactive_sboxes
    print("Total probability = p^2*q^2*r = 2^({:.2f}) x 2^({:.2f}) x r".format(diff_effect_upper*2, diff_effect_lower*2))
    print("2^({:.2f}) <= Total probability <= 2^({:.2f})".format(lower_bound, upper_bound))
    print("To compute the accurate value of total probability, r should be evaluated experimentally or using the (F)BCT framework")

    ##############################################################################################
    ##############################################################################################
    # write a file of result
    res = f"The {r0+rm+r1}-round distinguisher:\n"
    res += f"{r0}-round E0 part: \n"
    diff_upper_trail_values = map(str, diff_upper_trail.values())
    col_width = max(len(s) for s in diff_upper_trail_values) + 2
    for r in range(diff_upper_trail["nrounds"] + 1):
        res+=f"X{r}: "
        res += diff_upper_trail.get(f"x_{r}", 'none').ljust(col_width)
        res += diff_upper_trail.get(f"pr_{r}", 'none').ljust(col_width)
        res += '\n'
    common_active = middle_part["as"]
    constrained_active = middle_part["us"]
    res += f"{rm} round middle part:\n"
    res += f"number of common active S-box: {common_active}\n"
    res += f"number of constrained S-box: {constrained_active}\n"
    res += f"{r1}-round E1 part: \n"
    diff_lower_trail_values = map(str, diff_lower_trail.values())
    col_width = max(len(s) for s in diff_lower_trail_values) + 2
    for r in range(diff_lower_trail["nrounds"] + 1):
        res+=f"X{r+r0+rm}: "
        res += diff_lower_trail.get(f"x_{r}", 'none').ljust(col_width)
        res += diff_lower_trail.get(f"pr_{r}", 'none').ljust(col_width)
        res += '\n'
    with open("result.txt", "w") as restxt:
        restxt.write(res)

def loadparameters(args):
    """
    Get parameters from the argument list and inputfile.
    """

    # Load default values
    params = {"inputfile": "./input.yaml",
                "r0" : 4,
                "rm" : 7,
                "r1" : 3,
                "w0" : 6,
                "wDDT" : 1,
                "wFBCT" : 2,
                "wDDT2" : 4,
                "w1" : 6,
                "timelimit" : 1200,
                "numofsols" : 1}

    # Check if there is an input file specified
    if args.inputfile:
        with open(args.inputfile[0], 'r') as input_file:
            doc = yaml.load(input_file, Loader=yaml.FullLoader)
            params.update(doc)
            if "fixedVariables" in doc:
                fixed_vars = {}
                for variable in doc["fixedVariables"]:
                    fixed_vars = dict(list(fixed_vars.items()) +
                                    list(variable.items()))
                params["fixedVariables"] = fixed_vars

    # Override parameters if they are set on commandline
    
    if args.inputfile:
        params["inputfile"] = args.inputfile
    
    if args.r0 != None:
        params["r0"] = args.r0

    if args.rm != None:
        params["rm"] = args.rm

    if args.r1 != None:
        params["r1"] = args.r1

    if args.w0 != None:
        params["w0"] = args.w0

    if args.wDDT != None:
        params["wDDT"] = args.wDDT

    if args.wFBCT != None:
        params["wFBCT"] = args.wFBCT

    if args.wDDT2 != None:
        params["wDDT2"] = args.wDDT2

    if args.w1 != None:
        params["w1"] = args.w1
    
    if args.timelimit != None:
        params["timelimit"] = args.timelimit

    if args.numofsols != None:
        params["numofsols"] = args.numofsols

    return params

if __name__ == "__main__":
    main()
