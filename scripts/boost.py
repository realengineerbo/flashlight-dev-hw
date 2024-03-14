if __name__ == "__main__":
    # XHP50.3 HI min. and max. forward voltage (with safety margin)
    V_OUT_MIN = 4.5
    V_OUT_MAX = 8
    # LDO and ATtiny1616 DAC reference voltage
    VCC = 2.5
    # ATtiny1616 DAC resolution
    DAC_RESOLUTION = 256
    # Op-amp min. and max. output voltages
    V_OPAMP_MIN = 70e-6
    V_OPAMP_MAX = VCC - 70e-6
    # Op-amp worst case input offset voltage
    V_INPUT_OFFSET_MAX = 15e-6
    # MP3432 FB potential divider R1, datasheet recommended value
    FB_R1 = 750e3
    # MP3432 shutoff voltage (UVLO)
    V_UVLO = 2.25

    # User selected values
    # Op-amp inverting input potential divider, fixed lower leg
    R_B = 3.3e3  # Recommended by thefreeman
    # Current sense resistance
    R_SENSE = 10e-3
    # Max current
    I_MAX = 6

    # Calculated values
    # MP3432 FB potential divider R2 and series resistor R3
    FB_ALPHA = (min(V_UVLO, V_OPAMP_MAX) - V_OPAMP_MIN) / (V_OUT_MAX - V_OUT_MIN)
    FB_R3 = FB_R1 * FB_ALPHA
    FB_R2 = 1 / (((V_OUT_MAX - 1) / FB_R1) + ((V_OPAMP_MIN - 1) / FB_R3))
    # Peak op-amp non-inverting input voltage (current sense)
    VREF_MAX = I_MAX * R_SENSE
    # Op-amp inverting input potential divider, upper leg
    R_A = R_B * (VCC - VREF_MAX) / VREF_MAX
    # Theoretical lowest current setting
    REAL_I_OUT_MIN = I_MAX / DAC_RESOLUTION
    # 2nd current sense resistor for lower brightness
    R_SENSE_2 = VREF_MAX / REAL_I_OUT_MIN
    # Theoretical lowest current setting with 2nd current sense resistor
    REAL_I_OUT_MIN_2 = REAL_I_OUT_MIN / DAC_RESOLUTION
    # Op-amp input offset factor, should be >> 1
    OPAMP_INPUT_OFFSET_CHECK = (VREF_MAX / DAC_RESOLUTION) / V_INPUT_OFFSET_MAX

    print(f"FB_R2: {FB_R2}")
    print(f"FB_R3: {FB_R3}")
    print(f"VREF_MAX: {VREF_MAX}")
    print(f"R_A: {R_A}")
    print(f"I_OUT_MIN: {REAL_I_OUT_MIN}")
    print(f"R_SENSE_2: {R_SENSE_2}")
    print(f"I_OUT_MIN_2: {REAL_I_OUT_MIN_2}")
    print(f"OPAMP_INPUT_OFFSET_CHECK: {OPAMP_INPUT_OFFSET_CHECK}")

    # Actual component values
    FB_R2 = 130e3
    FB_R3 = 430e3
    R_A = 150e3  # Using 3.3k R_B
    R_SENSE_2 = 1

    REAL_VOUT_MAX = FB_R1 * (1 / FB_R2 - (V_OPAMP_MIN - 1) / FB_R3) + 1
    REAL_VOUT_MIN = FB_R1 * (1 / FB_R2 - (min(V_UVLO, V_OPAMP_MAX) - 1) / FB_R3) + 1
    REAL_VREF_MAX = VCC * R_B / (R_A + R_B)
    REAL_I_OUT_MAX = REAL_VREF_MAX / R_SENSE
    REAL_I_OUT_MIN = REAL_I_OUT_MAX / DAC_RESOLUTION
    REAL_I_OUT_MAX_2 = REAL_VREF_MAX / R_SENSE_2
    REAL_I_OUT_MIN_2 = REAL_I_OUT_MAX_2 / DAC_RESOLUTION
    REAL_OPAMP_INPUT_OFFSET_CHECK = (
        REAL_VREF_MAX / DAC_RESOLUTION
    ) / V_INPUT_OFFSET_MAX

    print(f"REAL_VOUT_MAX: {REAL_VOUT_MAX}")
    print(f"REAL_VOUT_MIN: {REAL_VOUT_MIN}")
    print(f"REAL_VREF_MAX: {REAL_VREF_MAX}")
    print(f"REAL_I_OUT_MAX: {REAL_I_OUT_MAX}")
    print(f"REAL_I_OUT_MIN: {REAL_I_OUT_MIN}")
    print(f"REAL_I_OUT_MAX_2: {REAL_I_OUT_MAX_2}")
    print(f"REAL_I_OUT_MIN_2: {REAL_I_OUT_MIN_2}")
    print(f"REAL_OPAMP_INPUT_OFFSET_CHECK: {REAL_OPAMP_INPUT_OFFSET_CHECK}")
