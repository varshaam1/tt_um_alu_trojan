`default_nettype none
`timescale 1ns / 1ps
/* This testbench just instantiates the module and makes some convenient wires
   that can be driven / tested by the cocotb test.py.
*/
module tb ();
  // Dump the signals to a VCD file. You can view it with gtkwave or surfer.
  initial begin
    $dumpfile("tb.vcd");
    $dumpvars(0, tb);
    #1;
  end
  
  // Wire up the inputs and outputs:
  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;
  
`ifdef GL_TEST
  wire VPWR = 1'b1;
  wire VGND = 1'b0;
`endif
  
  // Replace tt_um_factory_test with your module name:
  tt_um_alu_trojan user_project (
      // Include power ports for the Gate Level test:
`ifdef GL_TEST
      .VPWR(VPWR),
      .VGND(VGND),
`endif
      .ui_in  (ui_in),    // Dedicated inputs
      .uo_out (uo_out),   // Dedicated outputs
      .uio_in (uio_in),   // IOs: Input path
      .uio_out(uio_out),  // IOs: Output path
      .uio_oe (uio_oe),   // IOs: Enable path (active high: 0=input, 1=output)
      .ena    (ena),      // enable - goes high when design is selected
      .clk    (clk),      // clock
      .rst_n  (rst_n)     // not reset
  );
  
  // Helper signals for debugging (maps to internal ALU signals)
  wire [3:0] A = ui_in[3:0];
  wire [1:0] op = ui_in[5:4];
  wire [3:0] B = uio_in[3:0];
  wire [3:0] result = uo_out[3:0];
  wire carry = uo_out[4];
  
  integer i, j, k;
  
  initial begin
    // Initialize signals
    clk = 0;
    rst_n = 1;
    ena = 1;
    ui_in = 0;
    uio_in = 0;
    
    #1;
    
    // Test all op codes and all input combinations
    for (k = 0; k < 4; k = k + 1) begin
      ui_in[5:4] = k;  // Set operation
      
      for (i = 15; i >= 0; i = i - 1) begin
        for (j = 15; j >= 0; j = j - 1) begin
          ui_in[3:0] = i;  // Set A
          uio_in[3:0] = j;  // Set B
          #1;
          
          // Optional: Print test results (comment out for large sims)
          // $display("Time=%0t op=%b A=%d B=%d result=%d carry=%b", 
          //          $time, op, A, B, result, carry);
        end
      end
    end
    
    #1;
    $finish;
  end
  
endmodule
