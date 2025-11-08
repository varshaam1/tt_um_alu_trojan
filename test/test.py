# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


def calculate_expected(A, B, op):
    """Calculate expected ALU result and carry based on operation"""
    if op == 0:  # ADD
        result = A + B
        carry = 1 if result > 15 else 0
        result = result & 0xF
    elif op == 1:  # SUB
        result = A - B
        carry = 1 if result < 0 else 0
        result = result & 0xF
    elif op == 2:  # AND
        result = A & B
        carry = 0
    elif op == 3:  # OR
        result = A | B
        carry = 0
    else:
        result = 0
        carry = 0
    
    # Apply trojan effect: when A=15 and B=15, flip LSB and invert carry
    if A == 15 and B == 15:
        result = result ^ 0x1  # XOR with 0001
        carry = 1 - carry  # Invert carry
    
    return result, carry


@cocotb.test()
async def test_alu_all_operations(dut):
    """Test all ALU operations with all input combinations"""
    dut._log.info("Start ALU comprehensive test")
    
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Test all operations and input combinations
    error_count = 0
    test_count = 0
    trojan_triggers = 0
    
    for op in range(4):
        op_names = ["ADD", "SUB", "AND", "OR"]
        dut._log.info(f"Testing operation {op}: {op_names[op]}")
        
        for A in range(16):
            for B in range(16):
                # Set inputs
                # ui_in[3:0] = A, ui_in[5:4] = op
                # uio_in[3:0] = B
                dut.ui_in.value = (op << 4) | A
                dut.uio_in.value = B
                
                await ClockCycles(dut.clk, 1)
                
                # Get expected values
                expected_result, expected_carry = calculate_expected(A, B, op)
                
                # Read outputs
                # uo_out[3:0] = result, uo_out[4] = carry
                actual_result = int(dut.uo_out.value) & 0xF
                actual_carry = (int(dut.uo_out.value) >> 4) & 0x1
                
                # Check if trojan should trigger
                is_trojan = (A == 15 and B == 15)
                if is_trojan:
                    trojan_triggers += 1
                
                # Verify results
                if actual_result != expected_result or actual_carry != expected_carry:
                    dut._log.error(
                        f"FAIL: op={op_names[op]} A={A} B={B} "
                        f"Expected: result={expected_result} carry={expected_carry} "
                        f"Got: result={actual_result} carry={actual_carry} "
                        f"{'[TROJAN ACTIVE]' if is_trojan else ''}"
                    )
                    error_count += 1
                
                test_count += 1
    
    # Summary
    dut._log.info(f"Test completed: {test_count} tests")
    dut._log.info(f"Trojan triggered: {trojan_triggers} times")
    dut._log.info(f"Errors: {error_count}")
    
    assert error_count == 0, f"Test failed with {error_count} errors"


@cocotb.test()
async def test_alu_basic_operations(dut):
    """Test basic ALU operations with simple test cases"""
    dut._log.info("Start basic ALU test")
    
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Test ADD: 5 + 3 = 8
    dut._log.info("Test ADD: 5 + 3")
    dut.ui_in.value = (0 << 4) | 5  # op=ADD, A=5
    dut.uio_in.value = 3  # B=3
    await ClockCycles(dut.clk, 1)
    assert (int(dut.uo_out.value) & 0xF) == 8, "ADD 5+3 failed"
    
    # Test SUB: 10 - 4 = 6
    dut._log.info("Test SUB: 10 - 4")
    dut.ui_in.value = (1 << 4) | 10  # op=SUB, A=10
    dut.uio_in.value = 4  # B=4
    await ClockCycles(dut.clk, 1)
    assert (int(dut.uo_out.value) & 0xF) == 6, "SUB 10-4 failed"
    
    # Test AND: 12 & 10 = 8
    dut._log.info("Test AND: 12 & 10")
    dut.ui_in.value = (2 << 4) | 12  # op=AND, A=12
    dut.uio_in.value = 10  # B=10
    await ClockCycles(dut.clk, 1)
    assert (int(dut.uo_out.value) & 0xF) == 8, "AND 12&10 failed"
    
    # Test OR: 9 | 6 = 15
    dut._log.info("Test OR: 9 | 6")
    dut.ui_in.value = (3 << 4) | 9  # op=OR, A=9
    dut.uio_in.value = 6  # B=6
    await ClockCycles(dut.clk, 1)
    assert (int(dut.uo_out.value) & 0xF) == 15, "OR 9|6 failed"
    
    dut._log.info("Basic tests passed")


@cocotb.test()
async def test_trojan_trigger(dut):
    """Specifically test the trojan trigger condition"""
    dut._log.info("Start trojan trigger test")
    
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Test ADD with normal inputs: 15 + 14 = 29 (carry=1, result=13)
    dut._log.info("Test ADD: 15 + 14 (no trojan)")
    dut.ui_in.value = (0 << 4) | 15  # op=ADD, A=15
    dut.uio_in.value = 14  # B=14
    await ClockCycles(dut.clk, 1)
    result = int(dut.uo_out.value) & 0xF
    carry = (int(dut.uo_out.value) >> 4) & 0x1
    dut._log.info(f"Result: {result}, Carry: {carry}")
    assert result == 13 and carry == 1, "Normal operation failed"
    
    # Test ADD with trojan trigger: 15 + 15 = 30 normally (result=14, carry=1)
    # With trojan: result XOR 1 = 15, carry inverted = 0
    dut._log.info("Test ADD: 15 + 15 (TROJAN ACTIVE)")
    dut.ui_in.value = (0 << 4) | 15  # op=ADD, A=15
    dut.uio_in.value = 15  # B=15
    await ClockCycles(dut.clk, 1)
    result = int(dut.uo_out.value) & 0xF
    carry = (int(dut.uo_out.value) >> 4) & 0x1
    dut._log.info(f"Result: {result}, Carry: {carry}")
    assert result == 15 and carry == 0, "Trojan trigger failed"
    
    dut._log.info("Trojan trigger test passed")


@cocotb.test()
async def test_reset(dut):
    """Test reset functionality"""
    dut._log.info("Start reset test")
    
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Set some inputs and verify operation
    dut.ui_in.value = (0 << 4) | 7  # op=ADD, A=7
    dut.uio_in.value = 5  # B=5
    await ClockCycles(dut.clk, 1)
    assert (int(dut.uo_out.value) & 0xF) == 12
    
    # Apply reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Verify operation still works after reset
    dut.ui_in.value = (0 << 4) | 3  # op=ADD, A=3
    dut.uio_in.value = 4  # B=4
    await ClockCycles(dut.clk, 1)
    assert (int(dut.uo_out.value) & 0xF) == 7
    
    dut._log.info("Reset test passed")
