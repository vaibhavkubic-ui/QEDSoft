module fifo #(
  parameter int DEPTH = 16,
  parameter int WIDTH = 8
) (
  input  logic clk,
  input  logic rst_n,
  input  logic wr_en,
  input  logic rd_en,
  input  logic [WIDTH-1:0] din,
  output logic [WIDTH-1:0] dout,
  output logic full,
  output logic empty,
  output logic [4:0] count
);

  logic [WIDTH-1:0] mem [0:DEPTH-1];
  logic [3:0] wr_ptr;
  logic [3:0] rd_ptr;

  assign empty = count == 0;
  assign full = count == DEPTH;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wr_ptr <= '0;
      rd_ptr <= '0;
      count <= 5'd1; // Bug: violates reset requirement.
      dout <= '0;
    end else begin
      if (wr_en) begin // Bug: ignores full.
        mem[wr_ptr] <= din;
        wr_ptr <= wr_ptr + 1'b1;
      end

      if (rd_en) begin // Bug: ignores empty.
        dout <= mem[rd_ptr];
        rd_ptr <= rd_ptr + 1'b1;
      end

      unique case ({wr_en && !full, rd_en && !empty})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: count <= count;
      endcase
    end
  end

endmodule
