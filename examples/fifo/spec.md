# FIFO Natural-Language Specification

Module fifo has clock clk and active-low reset rst_n.

Inputs:
- input clk
- input rst_n
- input wr_en
- input rd_en
- input 8-bit din

Outputs:
- output 8-bit dout
- output full
- output empty
- output 5-bit count

Requirements:
- When reset is asserted, count must become zero.
- The FIFO must never read when empty.
- The FIFO must never write when full.
- Empty must be asserted when count is zero.
- Full must be asserted when count reaches depth.
- After a write when the FIFO is not full, count should increase on the next cycle.
- After a read when the FIFO is not empty, count should decrease on the next cycle.

Assumption:
- Assume wr_en and rd_en are synchronous to clk.
