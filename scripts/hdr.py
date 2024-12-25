import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm

plt.style.use("dark_background")
DPI = 120
FIGSIZE = (28, 9)

# Normal sense resistance is 1R
# HDR sense resistance is ~10mR (5mR + FET Rdson)
R_SENSE_1 = 1
R_SENSE_2 = 10e-3

# 53k6 and 1k potential divider for DAC to op-amp
R_A = 150e3
R_B = 3.3e3

# 8-bit DAC
DAC_MAX_VALUE = 255
DAC_VALUES = np.array(range(0, DAC_MAX_VALUE + 1))

# Available DAC reference values: 0.55, 1.1, 1.5, 2.5
DAC_VREFS = [0.55, 1.1, 1.5, 2.5]

# XHP50.3 HI, 5000K, CRI 90, Group H2
LM_PER_AMP = 996 / 1.4

# Use 32-bit brightness
BRIGHTNESS_MAX = 0xFFFFFFFF


def get_r_sense(is_hdr_on):
    if is_hdr_on:
        return R_SENSE_2
    else:
        return R_SENSE_1


def dac_to_v_inv(dac_value, dac_vref):
    "Converts DAC setting to op-amp inverting input voltage"
    v_dac = dac_value * dac_vref / DAC_MAX_VALUE
    return v_dac * R_B / (R_A + R_B)


def v_inv_to_i_led(v_inv, is_hdr_on):
    "Converts op-amp inverting input voltage to requested LED current"
    return v_inv / get_r_sense(is_hdr_on)


def remove_below_x(sorted_list, x):
    """Removes all elements in a sorted list below a given value."""
    # Use binary search to find the first index of an element >= x
    low = 0
    high = len(sorted_list) - 1
    while low <= high:
        mid = (low + high) // 2
        if sorted_list[mid] < x:
            low = mid + 1
        else:
            high = mid - 1

    # Slice the list from the found index to keep elements >= x
    return sorted_list[low:], low


def remove_above_x(sorted_list, x):
    """Removes all elements in a sorted list above a given value."""
    # Use binary search to find the first index of an element <= x
    low = 0
    high = len(sorted_list) - 1
    while low <= high:
        mid = (low + high) // 2
        if sorted_list[mid] <= x:
            low = mid + 1
        else:
            high = mid - 1

    # Slice the list from the found index to keep elements <= x
    return sorted_list[:low]


def dac_vref_to_enum(dac_vref):
    return "VREF_DAC0REFSEL_" + str(dac_vref).replace(".", "V") + "_gc"


def max_resolution(sorted_tuples):
    fig, axes = plt.subplots(nrows=1, ncols=3, dpi=DPI, figsize=FIGSIZE)
    fig.suptitle("Optimising for Resolution", fontsize=16)

    for (is_hdr_on, dac_vref), (i_leds, colour) in sorted_tuples:
        axes[0].plot(
            DAC_VALUES,
            i_leds,
            "x" if is_hdr_on else ".",
            label=f"VREF: {dac_vref} V, HDR: {is_hdr_on}",
            color=colour,
        )
    axes[0].set_xlabel("DAC value (LSB)")
    axes[0].set_ylabel("Current (A)")
    axes[0].set_yscale("log")
    axes[0].legend()

    i_min = 0
    i_leds_all = []
    groups = []
    for (is_hdr_on, dac_vref), (i_leds, colour) in sorted_tuples:
        i_leds_trunc, _ = remove_below_x(i_leds, i_min)
        groups.append((is_hdr_on, dac_vref, i_leds_trunc))

        # Store for next plot
        if i_leds_trunc[0] == i_min:
            i_leds_all.extend(i_leds_trunc[1:])
        else:
            i_leds_all.extend(i_leds_trunc)
        i_min = i_leds_trunc[-1]

        axes[1].plot(
            DAC_VALUES[-len(i_leds_trunc) :],
            i_leds_trunc,
            "x" if is_hdr_on else ".",
            label=f"VREF: {dac_vref} V, HDR: {is_hdr_on}",
            color=colour,
        )
    axes[1].set_xlabel("DAC value (LSB)")
    axes[1].set_ylabel("Current (A)")
    axes[1].set_yscale("log")
    axes[1].legend()

    print(
        f"min.: {1e6 * i_leds_all[0]:.2f}uA (~{LM_PER_AMP * i_leds_all[0]:.3f}lm), max. current: {i_leds_all[-1]:.2f}A (~{LM_PER_AMP * i_leds_all[-1]:.1f}lm)"
    )
    resolution = len(i_leds_all)
    print(f"resolution: {resolution}")

    axes[2].plot(range(len(i_leds_all)), i_leds_all, ".")
    axes[2].set_title(f"Brightness levels: {resolution}")
    axes[2].set_xlabel("Index")
    axes[2].set_ylabel("Current (A)")
    axes[2].set_yscale("log")

    # Calculate change in voltage drop across r_sense at boundary between HDR
    # We should see this change in boost driver's output voltage
    i_max_hdr_off = 0
    i_min_hdr_on = 0
    for is_hdr_on, dac_vref, i_leds_trunc in groups:
        # For calculating HDR output voltage change
        if not is_hdr_on:
            i_max_hdr_off = max(i_max_hdr_off, i_leds_trunc[-1])
        if is_hdr_on and i_min_hdr_on == 0:
            i_min_hdr_on = i_leds_trunc[0]
    delta_v = i_min_hdr_on * get_r_sense(True) - i_max_hdr_off * get_r_sense(False)
    print(f"delta_v: {1000 * delta_v}mV")

    for is_hdr_on, dac_vref, i_leds_trunc in groups:
        dac_value_step_count = len(i_leds_trunc) - 1
        dac_value_min = DAC_MAX_VALUE - dac_value_step_count
        brightness_min = int(BRIGHTNESS_MAX * i_leds_trunc[0] / i_leds_all[-1])
        brightness_max = int(BRIGHTNESS_MAX * i_leds_trunc[-1] / i_leds_all[-1])
        print(
            f"{{ .hdr = {str(is_hdr_on).lower()}, .dac_vref = {dac_vref_to_enum(dac_vref)}, .dac_value_min = {dac_value_min}, .dac_value_step_count = {dac_value_step_count}, .brightness_min = {brightness_min}U, .brightness_max = {brightness_max}U }},"
        )

    return groups, i_leds_all


def max_efficiency(sorted_tuples):
    _, axes = plt.subplots(nrows=1, ncols=3, dpi=DPI, figsize=FIGSIZE)
    plt.suptitle("Optimising for Efficiency", fontsize=16)

    # Find minimum current with HDR on
    i_min_hdr_on = 0

    for (is_hdr_on, dac_vref), (i_leds, colour) in sorted_tuples:
        if is_hdr_on and i_min_hdr_on == 0:
            i_min_hdr_on = i_leds[1]
        axes[0].plot(
            DAC_VALUES,
            i_leds,
            "x" if is_hdr_on else ".",
            label=f"VREF: {dac_vref} V, HDR: {is_hdr_on}",
            color=colour,
        )
    axes[0].set_xlabel("DAC value (LSB)")
    axes[0].set_ylabel("Current (A)")
    axes[0].set_yscale("log")
    axes[0].legend()

    i_min = 0
    i_leds_all = []
    groups = []
    for (is_hdr_on, dac_vref), (i_leds, colour) in sorted_tuples:
        if not is_hdr_on:
            i_leds = remove_above_x(i_leds, i_min_hdr_on)
        i_leds_trunc, dac_value_min = remove_below_x(i_leds, i_min)

        if len(i_leds_trunc) == 0:
            continue

        groups.append(
            (
                is_hdr_on,
                dac_vref,
                dac_value_min,
                i_leds_trunc,
            )
        )

        # Store for next plot
        if i_leds_trunc[0] == i_min:
            i_leds_all.extend(i_leds_trunc[1:])
        else:
            i_leds_all.extend(i_leds_trunc)
        i_min = i_leds_trunc[-1]

        axes[1].plot(
            DAC_VALUES[dac_value_min : dac_value_min + len(i_leds_trunc)],
            i_leds_trunc,
            "x" if is_hdr_on else ".",
            label=f"VREF: {dac_vref} V, HDR: {is_hdr_on}",
            color=colour,
        )
    axes[1].set_xlabel("DAC value (LSB)")
    axes[1].set_ylabel("Current (A)")
    axes[1].set_yscale("log")
    axes[1].legend()

    print(
        f"min.: {1e6 * i_leds_all[0]:.2f}uA (~{LM_PER_AMP * i_leds_all[0]:.3f}lm), max. current: {i_leds_all[-1]:.2f}A (~{LM_PER_AMP * i_leds_all[-1]:.1f}lm)"
    )
    resolution = len(i_leds_all)
    print(f"resolution: {resolution}")

    axes[2].plot(range(len(i_leds_all)), i_leds_all, ".")
    axes[2].set_title(f"Brightness levels: {resolution}")
    axes[2].set_xlabel("Index")
    axes[2].set_ylabel("Current (A)")
    axes[2].set_yscale("log")

    # Calculate change in voltage drop across r_sense at boundary between HDR
    # We should see this change in boost driver's output voltage
    i_max_hdr_off = 0
    i_min_hdr_on = 0
    for is_hdr_on, dac_vref, dac_value_min, i_leds_trunc in groups:
        # For calculating HDR output voltage change
        if not is_hdr_on:
            i_max_hdr_off = max(i_max_hdr_off, i_leds_trunc[-1])
        if is_hdr_on and i_min_hdr_on == 0:
            i_min_hdr_on = i_leds_trunc[0]
    delta_v = i_min_hdr_on * get_r_sense(True) - i_max_hdr_off * get_r_sense(False)
    print(f"delta_v: {1000 * delta_v}mV")

    for is_hdr_on, dac_vref, dac_value_min, i_leds_trunc in groups:
        dac_value_step_count = len(i_leds_trunc) - 1
        brightness_min = int(BRIGHTNESS_MAX * i_leds_trunc[0] / i_leds_all[-1])
        brightness_max = int(BRIGHTNESS_MAX * i_leds_trunc[-1] / i_leds_all[-1])
        print(
            f"{{ .hdr = {str(is_hdr_on).lower()}, .dac_vref = {dac_vref_to_enum(dac_vref)}, .dac_value_min = {dac_value_min}, .dac_value_step_count = {dac_value_step_count}, .brightness_min = {brightness_min}U, .brightness_max = {brightness_max}U }},"
        )

    return groups, i_leds_all


def lumens_to_value(groups, i_leds_all, lumens):
    current = lumens / LM_PER_AMP
    for is_hdr_on, dac_vref, dac_value_min, i_leds_trunc in groups:
        if i_leds_trunc[0] <= current <= i_leds_trunc[-1]:
            # Binary search for nearest value
            low = 0
            high = len(i_leds_trunc) - 1
            while low < high:
                mid = (low + high) // 2
                if mid == low or mid == high:
                    break
                if i_leds_trunc[mid] < current:
                    low = mid
                elif i_leds_trunc[mid] > current:
                    high = mid

            if low == high:
                index = low
            else:
                # Find nearer value
                abs_error_low = abs(current - i_leds_trunc[low])
                abs_error_high = abs(current - i_leds_trunc[high])
                if abs_error_low < abs_error_high:
                    index = low
                else:
                    index = high
            brightness = int(BRIGHTNESS_MAX * i_leds_trunc[index] / i_leds_all[-1])
            print(
                f"target: {1e3 * current:.2f}mA ({lumens}lm), nearest: {1e3 * i_leds_trunc[index]:.2f}mA (~{LM_PER_AMP * i_leds_trunc[index]:.2f}lm), brightness: {brightness}"
            )
            break


if __name__ == "__main__":
    configs = []
    for is_hdr_on in [False, True]:
        for dac_vref in DAC_VREFS:
            configs.append((is_hdr_on, dac_vref))

    colours = cm.rainbow(np.linspace(0, 1, len(configs)))

    lut = {}
    for (is_hdr_on, dac_vref), colour in zip(configs, colours):
        i_leds = v_inv_to_i_led(dac_to_v_inv(DAC_VALUES, dac_vref), is_hdr_on)
        lut[(is_hdr_on, dac_vref)] = (i_leds, colour)
    # Sort by peak current
    sorted_tuples = sorted(lut.items(), key=lambda item: item[1][0][-1])

    groups_resolution, i_leds_all_resolution = max_resolution(sorted_tuples)
    groups_efficiency, i_leds_all_efficiency = max_efficiency(sorted_tuples)

    lumens_to_value(groups_efficiency, i_leds_all_efficiency, 5)

    plt.show()
