/*
 * Copyright (C) 2002-2003  Pekka Enberg <penberg@iki.fi>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */
#ifndef _INDENT_H_
#define _INDENT_H_ 1

#include "buffer.h"
#include <stdbool.h>

/*
 * Indent options
 */
struct indent_options {
    char indent_char;
    int  num_indent_chars;
    bool force_newline_after_start_tag;
    bool force_newline_after_end_tag;
    bool force_newline_before_start_tag;
    bool force_newline_before_end_tag;
    bool force_always;
    int  max_columns;
    bool wrap_long_lines;
};

void indent_options_set_defaults(struct indent_options * opts);
void indent(FILE * input, FILE * output, struct indent_options * opts);

#endif
