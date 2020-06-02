import math
import xml.etree.ElementTree as ET

a_0 = 340.294               # speed of sound at MSL in standard atmosphere [m/s]
p_0 = 101325                # standard atmospheric pressure at MSL [Pa]
T_0 = 288.15                # standard atmospheric temperature at MSL [K]
rho_0 = 1.225               # standard atmospheric density at MSL [kg/m^3 ]
g_0 = 9.80665               # gravitational acceleration [m/s^2 ]
R = 287.05287               # real gas constant for air [m^2 /(K * s^2 )]
k = 1.4                     # adiabatic index of air [-]
beta_T_less = -0.0065        # ISA temperature gradient with altitude below the tropopause [K/m]

# BADA data:
m_ref = 0                   # reference mass [kg], from the PFM
MTOW = 0
OEW= 0
L_HV = 0                    # fuel lower heating value [m^2/s^2 ], from the PFM
fi = []                     # fi_1 ... fi_9 - idle rating fuel coefficients [-], from the TFM
f = []                      # f_1 ... f_25 - non-idle rating fuel coefficients [-], from the TFM
a = []                      # a_1 ... a_36 - non-idle rating thrust coefficients [-], from the TFM
b = []
c = []
kink = 0                    # kink point [K]
CPSFC = 0                   # power-specific fuel consumption coefficient
W_P_1_max_std_MSL  = 0      # maximum one-engine power in standard atmosphere at MSL [W],
                            # from the PEM where it is expressed in [hp]
n_eng = 0                   # number of engines of the aircraft
H_rho_turbo = 0             # altitude where the air density equals rho_turbo in standard atmosphere
engine_type = ''            # type of engine (turbofan, turboprop or piston)


# Calculate fuel on height h, speed is calculated using distance s and time t arguments
def calculate_fuel(aircraft_type, h, v, descent):

    global p_0, T_0, m_ref, g_0, a_0, L_HV, engine_type

    parse_bada(aircraft_type)

    delta = calculate_p(h) / p_0    # pressure ratio [-]
    THETA = calculate_T(h) / T_0    # temperature ratio [-]

    #print('delta')
    #print(delta)
    #print('THETA')
    #print(THETA)

    W_mref = m_ref * g_0            # weight force at m_ref [N]
    #print("mass")
    #print(m_ref)
    #m = int(OEW + 2/3 * (MTOW-OEW))
    #print(m)
    #W_mref = m * g_0



    if engine_type == 'JET':
        C_F = calculate_C_F_turbofan(h, v, descent, delta, THETA)
    elif engine_type == 'TURBOPROP':
        C_F = calculate_C_F_turboprop(h, v, descent, delta, THETA)
    elif engine_type == 'PISTON':
        C_F = calculate_C_F_piston(h, v, descent, W_mref, delta, THETA)
    else:
        C_F = 0

    fuel_flow = delta * math.sqrt(THETA) * W_mref * a_0 / L_HV *C_F
    log_file = open("temp.txt", "a+")
    log_file.write("W_mref = %f\r\n\n" % W_mref)
    log_file.write("a_0 = %f\r\n\n" % a_0)
    log_file.write("L_HV = %f\r\n\n" % L_HV)
    log_file.write("fuel_flow = %f\r\n\n" % fuel_flow)
    log_file.close()
    return delta * math.sqrt(THETA) * W_mref * a_0 / L_HV *C_F


# Calculate pressure p
def calculate_p(H_p_MSL):

    global beta_T_less, T_0, g_0, R, p_0

    p = p_0 * pow((T_0 + H_p_MSL * beta_T_less )/T_0, -g_0/(beta_T_less * R))
    return p


# Calculate temperature T, function of H_p_MSL - geopotential pressure altitude
def calculate_T(H_p_MSL):

    global T_0, beta_T_less
    return T_0 + beta_T_less*H_p_MSL


# Calculate Mach number M
def calculate_M(V_TAS, H_p_MSL):

    T = calculate_T(H_p_MSL)
    return V_TAS / math.sqrt(k*R*T)


def calculate_C_F_turbofan(h, v, descent, delta, THETA):

    global fi, f, k, a, b, c

    log_file = open("temp.txt", "a+")

    log_file.write("v = %f\r\n" % v)

    log_file.write("delta = %f\r\n" % delta)
    log_file.write("THETA = %f\r\n" % THETA)

    M = calculate_M(v, h)
    log_file.write("M = %f\r\n" % M)

    C_F = 0

    С_F_idle = ((fi[0] + fi[1]*delta + fi[2]*(delta**2) +
                (fi[3] + fi[4]*delta + fi[5]*(delta**2))*M +
                (fi[6] + fi[7]*delta + fi[8]*(delta**2))*M**2) * math.sqrt(THETA) / delta)

    if descent == 'true':
        C_F = С_F_idle
        log_file.write("descent\r\n")
        log_file.write("C_F_idle = %.3f\r\n" % C_F)

    else:
        delta_T = 0 # throttle parameter
        log_file.write("not descent\r\n")

        if (kink >= 0):
            delta_T = (b[0] + b[1]*M + b[2]*M**2 + b[3]*M**3 + b[4]*M**4 + b[5]*M**5 +
                      (b[6] + b[7]*M + b[8]*M**2 + b[9]*M**3 + b[10]*M**4 + b[11]*M**5)*delta +
                      (b[12] + b[13]*M + b[14]*M**2 + b[15]*M**3 + b[16]*M**4 + b[17]*M**5)*delta**2 +
                      (b[18] + b[19]*M + b[20]*M**2 + b[21]*M**3 + b[22]*M**4 + b[23]*M**5)*delta**3 +
                      (b[24] + b[25]*M + b[26]*M**2 + b[27]*M**3 + b[28]*M**4 + b[29]*M**5)*delta**4 +
                      (b[30] + b[31]*M + b[32]*M**2 + b[33]*M**3 + b[34]*M**4 + b[35]*M**5)*delta**5)
            log_file.write("kink >= 0\r\n")
            log_file.write("delta_T = %f\r\n" % delta_T)
        else:
            log_file.write("kink < 0\r\n")
            # total temperature ratio:
            THETA_t = THETA * (1 + M**2*(k-1)/2)
            delta_T = (c[0] + c[1]*M + c[2]*M**2 + c[3]*M**3 + c[4]*M**4 + c[5]*M**5 +
                      (c[6] + c[7]*M + c[8]*M**2 + c[9]*M**3 + c[10]*M**4 + c[11]*M**5)*THETA_t +
                      (c[12] + c[13]*M + c[14]*M**2 + c[15]*M**3 + c[16]*M**4 + c[17]*M**5)*THETA_t**2 +
                      (c[18] + c[19]*M + c[20]*M**2 + c[21]*M**3 + c[22]*M**4 + c[23]*M**5)*THETA_t**3 +
                      (c[24] + c[25]*M + c[26]*M**2 + c[27]*M**3 + c[28]*M**4 + c[29]*M**5)*THETA_t**4 +
                      (c[30] + c[31]*M + c[32]*M**2 + c[33]*M**3 + c[34]*M**4 + c[35]*M**5)*THETA_t**5)
            log_file.write("THETA_t = %f\r\n" % THETA_t)
            log_file.write("delta_T = %f\r\n" % delta_T)
        # thrust coefficient:
        C_T = (a[0] + a[1]*M + a[2]*M**2 + a[3]*M**3 + a[4]*M**4+ a[5]*M**5 +
              (a[6] + a[7]*M + a[8]*M**2 + a[9]*M**3 + a[10]*M**4+ a[11]*M**5) * delta_T +
              (a[12] + a[13]*M + a[14]*M**2 + a[15]*M**3 + a[16]*M**4+ a[17]*M**5) * delta_T**2 +
              (a[18] + a[19]*M + a[20]*M**2 + a[21]*M**3 + a[22]*M**4+ a[23]*M**5) * delta_T**3 +
              (a[24] + a[25]*M + a[26]*M**2 + a[27]*M**3 + a[28]*M**4+ a[29]*M**5) * delta_T**4 +
              (a[30] + a[31]*M + a[32]*M**2 + a[33]*M**3 + a[34]*M**4+ a[35]*M**5) * delta_T**5)
        log_file.write("C_T = %f\r\n" % C_T)
        C_F_gen = (f[0] + f[1]*C_T + f[2]*C_T**2 + f[3]*C_T**3 + f[4]*C_T**4 +
                  (f[5] + f[6]*C_T + f[7]*C_T**2 + f[8]*C_T**3 + f[9]*C_T**4)*M +
                  (f[10] + f[11]*C_T + f[12]*C_T**2 + f[13]*C_T**3 + f[14]*C_T**4)*M**2 +
                  (f[15] + f[16]*C_T + f[17]*C_T**2 + f[18]*C_T**3 + f[19]*C_T**4)*M**3 +
                  (f[20] + f[21]*C_T + f[22]*C_T**2 + f[23]*C_T**3 + f[24]*C_T**4)*M**4)
        log_file.write("C_F_gen = %f\r\n" % C_F_gen)

        C_F = max(С_F_idle, C_F_gen)
        log_file.write("C_F = %f\r\n" % C_F)
        log_file.close()
    return C_F


def calculate_C_F_turboprop(h, v, descent, delta, THETA):

    global fi, f, p, a
    # v = s/t
    M = calculate_M(v, h)

    C_F = 0
    C_F_idle = ((fi[0] + fi[1]*delta + fi[2]*delta**2 +
                (fi[3] + fi[4]*delta + fi[5]*delta**2)*M +
                (fi[6] + fi[7]*delta + fi[8]*delta**2)*M**2 +
                fi[9]*THETA + fi[10]*THETA**2 + fi[11]*M*THETA + fi[12]*M*delta*math.sqrt(THETA) +
                fi[13]*M*delta*THETA) / (delta * math.sqrt(THETA)))

    if descent == 'true':
        C_F = C_F_idle
    else:
        delta_T = (p[0] + p[1]*M + p[2]*M**2 + p[3]*M**3 + p[4]*M**4 + p[5]*M**5 +
                  (p[6] + p[7]*M + p[8]*M**2 + p[9]*M**3 + p[10]*M**4 + p[11]*M**5)*THETA +
                  (p[12] + p[13]*M + p[14]*M**2 + p[15]*M**3 + p[16]*M**4 + p[17]*M**5)*THETA**2 +
                  (p[18] + p[19]*M + p[20]*M**2 + p[21]*M**3 + p[22]*M**4 + p[23]*M**5)*THETA**3 +
                  (p[24] + p[25]*M + p[26]*M**2 + p[27]*M**3 + p[28]*M**4 + p[29]*M**5)*THETA**4 +
                  (p[30] + p[31]*M + p[32]*M**2 + p[33]*M**3 + p[34]*M**4 + p[35]*M**5)*THETA**5)

        C_P = (a[0] + a[1]*M + a[2]*M**2 + a[3]*M**3 + a[4]*M**4 + a[5]*M**5 +
              (a[6] + a[7]*M + a[8]*M**2 + a[9]*M**3 + a[10]*M**4 + a[11]*M**5)*delta_T +
              (a[12] + a[13]*M + a[14]*M**2 + a[15]*M**3 + a[16]*M**4 + a[17]*M**5)*delta_T**2 +
              (a[18] + a[19]*M + a[20]*M**2 + a[21]*M**3 + a[22]*M**4 + a[23]*M**5)*delta_T**3 +
              (a[24] + a[25]*M + a[26]*M**2 + a[27]*M**3 + a[28]*M**4 + a[29]*M**5)*delta_T**4 +
              (a[30] + a[31]*M + a[32]*M**2 + a[33]*M**3 + a[34]*M**4 + a[35]*M**5)*delta_T**5)

        C_F_gen = (f[0] + f[1]*C_P + f[2]*C_P**2 + f[3]*C_P**3 + f[4]*C_P**4 +
                  (f[5] + f[6]*C_P + f[7]*C_P**2 + f[8]*C_P**3 + f[9]*C_P**4)*M +
                  (f[10] + f[11]*C_P + f[12]*C_P**2 + f[13]*C_P**3 + f[14]*C_P**4)*M**2 +
                  (f[15] + f[16]*C_P + f[17]*C_P**2 + f[18]*C_P**3 + f[19]*C_P**4)*M**3 +
                  (f[20] + f[21]*C_P + f[22]*C_P**2 + f[23]*C_P**3 + f[24]*C_P**4)*M**4)

        C_F = max(C_F_idle, C_F_gen)

    return C_F


def calculate_C_F_piston(h, v, descent, W_mref, delta, THETA):

    global CPFSC, W_P_1_max_std_MSL, n_eng, H_rho_turbo, a0

    T = calculate_T(h)
    p = calculate_p(h)
    rho = p/(R*T)       #TODO: or read from BADA?
    sigma = rho / rho_0

    T_rho_turbo = calculate_T(H_rho_turbo)
    p_rho_turbo = calculate_p(H_rho_turbo)
    rho_turbo = p_rho_turbo/(R*T_rho_turbo)
    sigma_rho_turbo = rho_turbo / rho_0

    # maximum power coefficient in standard atmosphere at MSL:
    C_P_max_std_MSL = W_P_1_max_std_MSL * n_eng / (W_mref * a_0)

    # throttle parameter
    if descent == 'true':
        delta_T = 0
    else:
        delta_T = 1

    # power coefficient in standard atmosphere at MSL:
    C_P_std_MSL = C_P_max_std_MSL * delta_T

    C_P = 0

    if (sigma >= sigma_rho_turbo):
        C_P = C_P_std_MSL
    else:

        THETA_rho_turbo = T_rho_turbo / T_0
        delta_rho_turbo = p_rho_turbo / p_0

        C_P = min(C_P_std_MSL, C_P_max_std_MSL * delta * math.sqrt(THETA) * math.sqrt(THETA_rho_turbo) / delta_rho_turbo)

    C_F = CPFSC * C_P * math.sqrt(THETA) / delta

    return C_F


def parse_bada(aircraft_type):
    global m_ref, MTOW, OEW, L_HV, fi, f, a, b, c, p, kink, CPFSC, engine_type

    #TODO: filename from aircraft_type
    #filename = getFilename(aircraft_type)
    #filename = 'A320-232.xml'
    filename = 'B738W26.xml'

    tree = ET.parse(filename)
    root = tree.getroot()

    for type in root.findall("./type"):
        engine_type = type.text                         # type of engine (turbofan, turboprop or piston)

    for mref in root.findall("./PFM/MREF"):
        m_ref = int(mref.text)                          # reference mass [kg], from the PFM

    for mtow in root.findall("./ALM/DLM/MTOW"):
        MTOW = int(mtow.text)                           # maximum take-off weight, from the ALM

    for oew in root.findall("./ALM/DLM/OEW"):
        OEW = int(oew.text)                             # operating empty weight, from the ALM

    for lhv in root.findall("./PFM/LHV"):
        L_HV = int(lhv.text)                            # fuel lower heating value [m^2/s^2 ], from the PFM


    for element in root.findall("./PFM/TFM/LIDL/CF/fi"):
        fi.append(float(element.text))                  # fi_1 ... fi_9 - idle rating fuel coefficients [-], from the TFM
    for element in root.findall("./PFM/TFM/CF/f"):
        f.append(float(element.text))                   # f_1 ... f_25 - non-idle rating fuel coefficients [-], from the TFM
    for element in root.findall("./PFM/TFM/CT/a"):
        a.append(float(element.text))                   # a_1 ... a_36 - non-idle rating thrust coefficients [-], from the TFM
    for element in root.findall("./PFM/TFM/MCMB/kink"):
        kink = int(element.text)                        # kink point [K]
    for element in root.findall("./PFM/TFM/MCMB/flat_rating/b"):
        b.append(float(element.text))
    for element in root.findall("./PFM/TFM/MCMB/temp_rating/c"):
        c.append(float(element.text))

    for number_eng in root.findall("./PFM/n_eng"):
        n_eng = int(number_eng.text)
    for h_rho_turbo in root.findall("./PFM/PEM/Hd_turbo"):
        H_rho_turbo = int(h_rho_turbo.text)             # altitude where the air density equals rho_turbo in standard atmosphere
    for cpsfc in root.findall("./PFM/PEM/CPSFC"):
        CPSFC = float(cpsfc.text)                       # power-specific fuel consumption coefficient
    for max_eff in root.findall("./PFM/PEM/max_eff"):
        #TODO: convert max_eff from hp to W ?
        W_P_1_max_std_MSL = float(max_eff.text)         # maximum one-engine power in standard atmosphere at MSL [W],
                                                        # from the PEM where it is expressed in [hp]
