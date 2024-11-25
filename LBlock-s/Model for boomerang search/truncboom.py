from truncdiff import WordLBlock
import time
from gurobipy import *

class TruncatedBoomerang(WordLBlock):
    """
    This class is used to find a truncated boomerang trail for LBlock block cipher
    """

    count = 0
    def __init__(self, r0, r1, rm, w0=1, w1=1, wDDT=1, wFBCT=1, wDDT2=1):
        """
        Initialize the main parameters of the boomerang trails

        :param r0 int: number of rounds covered by only the upper trail
        :param r1 int: number of rounds covered by only the lower trail
        :param rm int: number of rounds covered by both the lower and upper trails (middle part)
        :param w0 int: cost of active S-boxes in the upper trail
        :param w1 int: cost of active S-boxes in the lower trail
        :param wm int: cost of common active S-boxes between the upper and lower trails
        """

        super().__init__()
        self.lp_file_name = f"lblock_{r0}_{rm}_{r1}.lp"
        self.r0 = r0
        self.R0 = r0 + rm
        self.r1 = r1
        self.R1 = r1 + rm
        self.rm = rm
        self.w0 = w0
        self.w1 = w1
        self.wDDT = wDDT
        self.wFBCT = wFBCT
        self.wDDT2 = wDDT2
        self.iterative = False

    def constraint_by_xor(self, a, b, c):
        """
        operation:
        (a, b) |----> c = a + b
        model:
        c - a >= 0
        c - b >= 0
        a + b - c >= 0
        """

        constraints = ""
        constraints += f"{c} - {a} >= 0\n"
        constraints += f"{c} - {b} >= 0\n"
        constraints += f"{a} + {b} - {c} >= 0\n"
        return constraints

    def generate_upper_constraints(self):
        """
        Generate the constraints describing the propagation of
        upper differential trail
        """
        constraints = ""
        for rn in range(self.R0):
            x_in = self.generate_round_x_variables(rn, ul="u")
            x_out = self.generate_round_x_variables(rn + 1, ul="u")
            x_middle = self.swap(x_out)
            sbo = self.apply_permutation(x_in[0:8])
            for n in range(8):
                constraints += self.constraints_by_equality(x_in[n], x_middle[n])
                if rn < self.r0:
                    constraints += self.constraint_by_trunc_xor(sbo[n], x_in[8 + (n + 2)%8], x_middle[8 + n])
                else:
                    constraints += self.constraint_by_xor(sbo[n], x_in[8 + (n + 2)%8], x_middle[8 + n])
        return constraints

    def generate_lower_constraints(self):
        """
        Generate the constraints describing the propagation of
        lower differential trail
        """

        constraints = ""
        for rn in range(self.R1):
            x_in = self.generate_round_x_variables(rn, ul="l")
            x_out = self.generate_round_x_variables(rn + 1, ul="l")
            x_middle = self.swap(x_out)
            sbo = self.apply_permutation(x_in[0:8])
            for n in range(8):
                constraints += self.constraints_by_equality(x_in[n], x_middle[n])
                if rn < self.rm:
                    constraints += self.constraint_by_xor(sbo[n], x_middle[8 + n], x_in[8 + (n + 2)%8])
                else:
                    constraints += self.constraint_by_trunc_xor(sbo[n], x_in[8 + (n + 2)%8], x_middle[8 + n])
        return constraints

    def generate_linking_vars(self, rn):
        """
        Generate linking variables to model the common active
        S-boxes between upper and lower trails
        """

        s = [f"s_{rn}_{n}" for n in range(8)]
        self.milp_variables.extend(s)
        return s

    def generate_random_vars(self, rn, ul='u'):
        rvar = [f"{ul}_ran_{rn}_{n}" for n in range (16)]
        self.milp_variables.extend(rvar)
        return rvar
    
    def generate_used_vars(self, rn, ul='u'):
        uvar = [f"{ul}_used_{rn}_{n}" for n in range (8)]
        self.milp_variables.extend(uvar)
        return uvar

    def generate_tables_vars(self, rn, tb='FBCT'):
        tbvar = [f"{tb}_{rn}_{n}" for n in range (8)]
        self.milp_variables.extend(tbvar)
        return tbvar

    def generate_objective_function(self):
        """
        Generate objective function of MILP model
        """

        upper_active_sboxes = []

        for r in range(0, self.r0):
            xu = self.generate_round_x_variables(rn=r, ul="u")
            for i in range(8):
                upper_active_sboxes.append(f"{self.w0} {xu[i]}")
        lower_active_sboxes = []
        for r in range(self.rm, self.R1):
            xl = self.generate_round_x_variables(rn=r, ul="l")
            for i in range(8):
                lower_active_sboxes.append(f"{self.w1} {xl[i]}")
        DDT_sboxes = []
        for r in range(self.rm):
            s = self.generate_tables_vars(r, tb='DDT')
            for i in range(8):
                DDT_sboxes.append(f"{self.wDDT} {s[i]}")
        FBCT_sboxes = []
        for r in range(self.rm):
            s = self.generate_tables_vars(r, tb='FBCT')
            for i in range(8):
                FBCT_sboxes.append(f"{self.wFBCT} {s[i]}")
        DDT2_sboxes = []
        for r in range(self.rm):
            s = self.generate_tables_vars(r, tb='DDT2')
            for i in range(8):
                DDT2_sboxes.append(f"{self.wDDT2} {s[i]}")
        if upper_active_sboxes == [] and lower_active_sboxes == []:
            objective  = " + ".join(DDT_sboxes) + " + " + \
                         " + ".join(FBCT_sboxes) + " + " + \
                         " + ".join(DDT2_sboxes)
        elif upper_active_sboxes == []:
            objective  = " + ".join(lower_active_sboxes) + " + " + \
                         " + ".join(DDT_sboxes) + " + " + \
                         " + ".join(FBCT_sboxes) + " + " + \
                         " + ".join(DDT2_sboxes)
        elif lower_active_sboxes == []:
            objective  = " + ".join(upper_active_sboxes) + " + " + \
                         " + ".join(DDT_sboxes) + " + " + \
                         " + ".join(FBCT_sboxes) + " + " + \
                         " + ".join(DDT2_sboxes)
        else:
            objective  = " + ".join(upper_active_sboxes) + " + " + \
                         " + ".join(lower_active_sboxes) + " + " + \
                         " + ".join(DDT_sboxes) + " + " + \
                         " + ".join(FBCT_sboxes) + " + " + \
                         " + ".join(DDT2_sboxes)
        return objective
    
    def generate_upper_random_constraints(self):
        constraints = ""
        start = self.r0
        uran = self.generate_random_vars(0, ul='u')
        for i in range (16):
            constraints += f"{uran[i]} = 0\n"
        for rn in range (1, self.rm):
            uran0 = uran
            uran = self.generate_random_vars(rn, ul='u')
            xu = self.generate_round_x_variables(start + rn - 1, ul='u')
            for i in range (8):
                y0 = self.ipermute_nibbles[i]
                y1 = self.irot_nibbles[i] + 8
                constraints += f"{xu[y0]} + {uran0[y1]} - {uran[i]} >= 0\n"
                constraints += f"{uran0[y0]} + {xu[y1]} - {uran[i]} >= 0\n"
                constraints += f"{uran[i]} - {xu[y0]} - {xu[y1]} >= -1\n"
                constraints += f"{uran[i]} - {uran0[y0]} >= 0\n"
                constraints += f"{uran[i]} - {uran0[y1]} >= 0\n"
                constraints += f"{uran[i + 8]} - {uran0[i]} = 0\n"
        return constraints
    
    def generate_lower_random_constraints(self):
        constraints = ""
        lran = self.generate_random_vars(self.rm, ul='l')
        for i in range (16):
            constraints += f"{lran[i]} = 0\n"
        for r in range (1, self.rm):
            rn = self.rm - r
            lran0 = lran
            lran = self.generate_random_vars(rn, ul='l')
            lu = self.generate_round_x_variables(rn + 1, ul='l')
            for i in range (8):
                y = i + 8
                y0 = self.rot_nibbles[i]
                y1 = self.ipermute_nibbles[y0] + 8
                constraints += f"{lu[y0]} + {lran0[y1]} - {lran[y]} >= 0\n"
                constraints += f"{lran0[y0]} + {lu[y1]} - {lran[y]} >= 0\n"
                constraints += f"{lran[y]} - {lu[y0]} - {lu[y1]} >= -1\n"
                constraints += f"{lran[y]} - {lran0[y0]} >= 0\n"
                constraints += f"{lran[y]} - {lran0[y1]} >= 0\n"
                constraints += f"{lran[i]} - {lran0[i + 8]} = 0\n"
        return constraints
    
    def generate_more_random_constraints(self):
        constraints = ""
        for rn in range (self.rm):
            uran = self.generate_random_vars(rn, ul='u')
            lran = self.generate_random_vars(rn + 1, ul='l')
            for i in range (8):
                yu = i
                yl = i + 8
                constraints += f"- {uran[yu]} - {lran[yl]} >= -1\n"
        return constraints
    
    def generate_upper_used_constraints(self):
        constraints = ""
        uran = []
        svar = []
        uisu = []
        for rn in range (self.rm):
            uran.append(self.generate_random_vars(rn, ul="u"))
            svar.append(self.generate_linking_vars(rn))
            uisu.append(self.generate_used_vars(rn, ul="u"))
        for i in range (8):
            constraints += f"{uisu[self.rm - 1][i]} = 0\n"
        for rn in range (self.rm - 1):
            for i in range (8):
                temp = ""
                y = self.permute_nibbles[i]
                constraints += f"- {uisu[rn][i]} - {uran[rn][i]} >= -1\n"
                constraints += f"xu_{self.r0 + rn}_{i} - {uisu[rn][i]} >= 0\n"
                for rs in range (rn + 1, self.rm, 2):
                    constraints += f"{uisu[rn][i]} - {svar[rs][y]} + {uran[rs][y]} - xu_{self.r0 + rn}_{i} >= -1\n"
                    constraints += f"{uisu[rn][i]} - {uisu[rs][y]} + {uran[rs][y]} - xu_{self.r0 + rn}_{i} >= -1\n"
                    constraints += f"- {uisu[rn][i]} - {uran[rs][y]}" + temp + " >= -1\n"
                    temp += f" + {svar[rs][y]} + {uisu[rs][y]}"
                    y = self.rot_nibbles[y]
                constraints += f"- {uisu[rn][i]}" + temp + " >= 0\n"
        return constraints

    def generate_lower_used_constraints(self):
        constraints = ""
        lran = []
        svar = []
        lisu = []
        lran.append([])
        for rn in range (self.rm):
            lran.append(self.generate_random_vars(rn + 1, ul="l"))
            svar.append(self.generate_linking_vars(rn))
            lisu.append(self.generate_used_vars(rn, ul="l"))
        for i in range (8):
            constraints += f"{lisu[0][i]} = 0\n"
        for rn in range (1, self.rm):
            for i in range (8):
                temp = ""
                y = self.irot_nibbles[self.permute_nibbles[i]]
                constraints += f"- {lisu[rn][i]} - {lran[rn][i]} >= -1\n"
                constraints += f"xl_{rn}_{i} - {lisu[rn][i]} >= 0\n"
                for r in range (0, rn, 2):
                    rs = rn - r
                    y0 = y + 8
                    constraints += f"{lisu[rn][i]} - {svar[rs - 1][y]} + {lran[rs][y0]} - xl_{rn}_{i} >= -1\n"
                    constraints += f"{lisu[rn][i]} - {lisu[rs - 1][y]} + {lran[rs][y0]} - xl_{rn}_{i} >= -1\n"
                    constraints += f"- {lisu[rn][i]} - {lran[rs][y0]}" + temp + " >= -1\n"
                    temp += f" + {svar[rs - 1][y]} + {lisu[rs - 1][y]}"
                    y = self.irot_nibbles[y]
                constraints += f"- {lisu[rn][i]}" + temp + " >= 0\n"
        return constraints

    def generate_DDT_constraints(self):
        constraints = ""
        for rn in range (self.rm):
            ddt = self.generate_tables_vars(rn, tb='DDT')
            svar = self.generate_linking_vars(rn)
            uisu = self.generate_used_vars(rn, ul='u')
            lisu = self.generate_used_vars(rn, ul='l')
            for i in range (8):
                constraints += f"- {ddt[i]} - {svar[i]} >= -1\n"
                constraints += f"{ddt[i]} + 2 {svar[i]} - {uisu[i]} - {lisu[i]} >= 0\n"
                constraints += f"{uisu[i]} + {lisu[i]} - {ddt[i]} >= 0\n"
        return constraints
    
    def generate_FBCT_constraints(self):
        constraints = ""
        for rn in range (self.rm):
            fbct = self.generate_tables_vars(rn, tb='FBCT')
            svar = self.generate_linking_vars(rn)
            uran = self.generate_random_vars(rn, ul='u')
            lran = self.generate_random_vars(rn + 1, ul='l')
            for i in range (8):
                yu = i
                yl = i + 8
                constraints += f"{svar[i]} - {fbct[i]} >= 0\n"
                constraints += f"{fbct[i]} - {svar[i]} + {uran[yu]} + {lran[yl]} >= 0\n"
                constraints += f"- {fbct[i]} - {uran[yu]} >= -1\n"
                constraints += f"- {fbct[i]} - {lran[yl]} >= -1\n"
        return constraints
    
    def generate_DDT2_constraints(self):
        constraints = ""
        for rn in range (self.rm):
            ddt2 = self.generate_tables_vars(rn, tb='DDT2')
            svar = self.generate_linking_vars(rn)
            uran = self.generate_random_vars(rn, ul='u')
            lran = self.generate_random_vars(rn + 1, ul='l')
            for i in range (8):
                yu = i
                yl = i + 8
                constraints += f"{svar[i]} - {ddt2[i]} >= 0\n"
                constraints += f"{uran[yu]} + {lran[yl]} - {ddt2[i]} - {svar[i]} >= -1\n"
                constraints += f"{ddt2[i]} - {svar[i]} - {uran[yu]} - {lran[yl]} >= -1\n"
        return constraints


    def make_model(self):
        """
        Generate the main constrain of our MILP model
        describing the propagation of differential trails in upper and
        lower parts
        """

        constraints = "minimize\n"
        constraints += self.generate_objective_function()
        constraints += "\nsubject to\n"
        constraints += self.generate_upper_constraints()
        constraints += self.exclude_trivial_solution(ul="u")
        constraints += self.generate_lower_constraints()
        constraints += self.exclude_trivial_solution(ul="l")
        constraints += self.generate_upper_random_constraints()
        constraints += self.generate_lower_random_constraints()
        constraints += self.generate_more_random_constraints()
        constraints += self.generate_upper_used_constraints()
        constraints += self.generate_lower_used_constraints()
        constraints += self.generate_DDT_constraints()
        constraints += self.generate_FBCT_constraints()
        constraints += self.generate_DDT2_constraints()

        for rn in range(self.rm):
            s = self.generate_linking_vars(rn)
            xu = self.generate_round_x_variables(rn + self.r0, ul="u")
            xl = self.generate_round_x_variables(rn, ul="l")
            for i in range(8):
                constraints += f"{xu[i]} - {s[i]} >= 0\n"
                constraints += f"{xl[i]} - {s[i]} >= 0\n"
                constraints += f"- {xu[i]} - {xl[i]} + {s[i]} >= -1\n"
        if self.iterative == True:
            x_in = self.generate_round_x_variables(0, ul="u")
            # x_out = self.generate_round_x_variables(self.R1, ul="l")
            x_out = self.generate_round_x_variables(self.rm, ul="u")
            for i in range(16):
                constraints += f"{x_in[i]} - {x_out[i]} = 0\n"
        constraints += self.declare_binary_vars()
        constraints += "end"
        with open(self.lp_file_name, "w") as lpfile:
            lpfile.write(constraints)

    def find_truncated_boomerang_trail(self):
        """
        Solve the constructed model minimizing the number of active S-boxes
        """

        self.make_model()
        self.milp_model = read(self.lp_file_name)
        os.remove(self.lp_file_name)
        self.milp_model.setParam(GRB.Param.OutputFlag, True)
        
        self.milp_model.Params.PoolSearchMode = 2
        # Limit number of solutions
        self.milp_model.Params.PoolSolutions = 10
        # Choose solution number 1
        self.milp_model.Params.SolutionNumber = 0
        
        start_time = time.time()
        ###################
        self.milp_model.optimize()
        ###################
        elapsed_time = time.time() - start_time
        time_line = "Total time to find the trail: %0.02f seconds\n".format(elapsed_time)
        objective_function = self.milp_model.getObjective()
        objective_value = objective_function.getValue()
        print(f"Number of active S-boxes: {objective_value}")

    def parse_solver_output(self):
        '''
        Extract the truncated differential characteristic from the solver output
        '''

        self.upper_trail = dict()
        self.lower_trail = dict()
        self.middle_part = dict()
        get_value_str = lambda t: str(int(self.milp_model.getVarByName(t).Xn))
        get_value_int = lambda t: int(self.milp_model.getVarByName(t).Xn)

        print("\nUpper Truncated Trail:\n")
        for r in range(self.R0 + 1):
            x_name = self.generate_round_x_variables(rn=r, ul="u")
            x_value = ''.join(list(map(get_value_str, x_name)))
            x_value0 = '[' + ', '.join(list(map(get_value_str, x_name))) + '],'
            self.upper_trail[f"x_{r}"] = x_value
            print(x_value0)
        print("\n%s\n%s" % ("+"*16, "#"*16))
        print("Lower Truncated Trail:\n")
        for r in range(self.R1 + 1):
            x_name = self.generate_round_x_variables(rn=r, ul="l")
            x_value = ''.join(list(map(get_value_str, x_name)))
            x_value0 = '[' + ', '.join(list(map(get_value_str, x_name))) + '],'
            self.lower_trail[f"x_{r}"] = x_value
            print(x_value0)
        print("\n%s\n%s" % ("#"*16, "#"*16))
        print("Middle Part:\n")
        for r in range(self.rm):
            s_name = self.generate_linking_vars(r)
            s_value = '*'.join(list(map(get_value_str, s_name))) + "*"
            s_value0 = '[' + ', '.join(list(map(get_value_str, s_name))) + "],"
            self.middle_part[f"s_{r}"] = s_value
            print(s_value0)
        s = []
        for r in range(self.rm):
            s.extend(self.generate_linking_vars(r))
        ncs = sum(list(map(get_value_int, s)))
        print(f"\nNumber of common active S-boxes: {ncs}")
        self.middle_part["as"] = ncs
        return self.upper_trail, self.middle_part, self.lower_trail

if __name__ == "__main__":
    r0, rm, r1 = 2, 8, 2
    w0, wDDT, wFBCT, wDDT2, w1 = 6, 2, 3, 4, 6
    bm = TruncatedBoomerang(r0=r0, r1=r1, rm=rm, w0=w0, w1=w1, wDDT=wDDT, wFBCT=wFBCT, wDDT2=wDDT2)
    bm.iterative = False
    bm.find_truncated_boomerang_trail()
    bm.parse_solver_output()