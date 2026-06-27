function [count_next, empty_next, full_next] = fifo_step(wr_en, rd_en, full, empty, count)
% FIFO golden-model step used by QEDSoft Job 1.
if wr_en && ~full
    count_next = count + 1;
elseif rd_en && ~empty
    count_next = count - 1;
else
    count_next = count;
end

empty_next = count_next == 0;
full_next = count_next == 16;
end
