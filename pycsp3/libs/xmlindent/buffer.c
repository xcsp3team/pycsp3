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
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include "error.h"
#include "buffer.h"

/* Initialize buffer.  */
void buffer_init(struct buffer * buffer, size_t initial_capacity)
{
    buffer->data     = malloc(initial_capacity * sizeof(unsigned char));
    buffer->length   = 0;
    buffer->capacity = initial_capacity;
}

/* Release buffer.  */
void buffer_release(struct buffer * buffer)
{
    if (buffer->capacity > 0) {
	free(buffer->data);
	buffer->data     = NULL;
	buffer->capacity = 0;
    }
    buffer->length = 0;
}

/* Check if buffer is full.  */
bool buffer_is_full(struct buffer * buffer)
{
    return (buffer->capacity == buffer->length);
}

#define BUFFER_GROWTH_INCREMENT 256

/* Grow buffer by one.  */
void buffer_grow(struct buffer * buffer)
{
    buffer->data =
	realloc(buffer->data,
		(buffer->capacity +
		 BUFFER_GROWTH_INCREMENT) * sizeof(unsigned char));

    if (buffer->data == NULL) {
	error("Could not allocate memory for buffer.");
	exit(1);
    }
    buffer->capacity += BUFFER_GROWTH_INCREMENT;
}

/* Push character at the end of buffer.  */
void buffer_push_char(struct buffer * buffer, int c)
{
    if (buffer_is_full(buffer)) {
	buffer_grow(buffer);
    }
    buffer->data[buffer->length] = c;
    buffer->length++;
}

/* Push string at the end of buffer.  */
void buffer_push_str(struct buffer * buffer, const char * text)
{
    int i;

    for (i = 0; i < strlen(text); i++) {
	buffer_push_char(buffer, (int) text[i]);
    }
}

/* Pop item from back of buffer.  */
int buffer_pop_char(struct buffer * buffer)
{
    int result = -1;

    if (buffer->length > 0) {
	buffer->length--;
	result = buffer->data[buffer->length];
    } else {
	error("Buffer underflow.");
    }
    return result;
}

/* Flush buffer to output stream.  */
void buffer_flush(struct buffer * buffer, FILE * output)
{
    int i;

    for (i = 0; i < buffer->length; i++) {
	fputc(buffer->data[i], output);
    }
    buffer->length = 0;
}

/* Return buffer size.  */
size_t buffer_size(struct buffer * buffer)
{
    return buffer->length;
}

void buffer_copy(struct buffer * dest, struct buffer * src)
{
    int i;

    for (i = 0; i < src->length; i++) {
        buffer_push_char(dest, src->data[i]);
    }
}

void buffer_clear(struct buffer * buf)
{
    buf->length = 0;
}
