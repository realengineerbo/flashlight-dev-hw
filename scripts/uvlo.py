"""MP3432 UVLO potential divider calculation"""

if __name__ == "__main__":
    V_IN_ON = 2.35
    V_IN_OFF = 2.25

    # From datasheet
    # V_IN_UVLO_HYS = 5e-6 * R_TOP
    # V_IN_ON = V_EN_ON * (1 + (R_TOP / R_BOTTOM)) + V_IN_UVLO_HYS
    V_EN_ON = 1.23

    V_IN_UVLO_HYS = V_IN_ON - V_IN_OFF
    R_TOP = V_IN_UVLO_HYS / 5e-6
    R_BOTTOM = R_TOP / (((V_IN_ON - V_IN_UVLO_HYS) / V_EN_ON) - 1)

    print(R_TOP)
    print(R_BOTTOM)
