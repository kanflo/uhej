/* 
 * The MIT License (MIT)
 * 
 * Copyright (c) 2017 Johan Kanflo (github.com/kanflo)
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <stdio.h>
#include "hexdump.h"

/**
  * @brief Dump data in hex format, DUMP_LINE_WIDTH on each line
  * @param buf pointer to data
  * @param len length of data
  * @retval none
  */
void hexdump(uint8_t *buf, uint32_t len)
{
    uint32_t i, j, last_line = 0;
    for(i=0; i<len; i++) {
        if (i && !(i%DUMP_LINE_WIDTH)) {
            printf("   ");
            for(j = 0; j < DUMP_LINE_WIDTH && last_line+j < len; j++) {
                printf("%c", (buf[last_line+j]<' ' || buf[last_line+j]>'~') ? '.' : buf[last_line+j]);
            }
            printf("\n");
            last_line = i;
        }
        printf(" %02x", buf[i]);
    }
    if (i && (i%DUMP_LINE_WIDTH)) {
        printf("   ");
        for(j = i%DUMP_LINE_WIDTH; j<DUMP_LINE_WIDTH; j++) {
            printf("   ");
        }
        for(uint32_t j = 0; j < DUMP_LINE_WIDTH && last_line+j < len; j++) {
            printf("%c", (buf[last_line+j]<' ' || buf[last_line+j]>'~') ? '.' : buf[last_line+j]);
        }
        printf("\n");
    }
    printf("\n");
}
