/*
 * Copyright (C) 2002  Pekka Enberg <penberg@iki.fi>
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
#ifndef _BUFFER_H_
#define _BUFFER_H_ 1

#include <stdbool.h>
#include <stdio.h>
#include <stddef.h>

/* Buffer used to hold XML stream.  */
struct buffer {
    char * data;
    size_t length;
    size_t capacity;
};

void buffer_init(struct buffer * buffer, size_t initial_capacity);
void buffer_release(struct buffer * buffer);
void buffer_push_str(struct buffer * buffer, const char * text);
void buffer_push_char(struct buffer * buffer, int c);
int buffer_pop_char(struct buffer * buffer);
void buffer_flush(struct buffer * buffer, FILE * output);
void buffer_copy(struct buffer * dest, struct buffer * src);
void buffer_clear(struct buffer * buf);
size_t buffer_size(struct buffer * buffer);

#endif
