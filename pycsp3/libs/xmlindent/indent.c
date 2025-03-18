/*
 * Copyright (C) 2002-2004  Pekka Enberg <penberg@iki.fi>
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
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "buffer.h"
#include "indent.h"

/*
 * Functions the generated scanner uses. 
 */
static void xml_declaration(void);
static void cdata_section(void);
static void doctype_declaration(void);
static void start_tag(void);
static void end_tag(void);
static void empty_element_tag(void);
static void comment(void);
static void content(void);
static void processing_insn(void);
static void do_newline(struct buffer * buffer, const char * text);

#include "lex.yy.c"

/*
 * Flex unput() wrapper
 */
extern void do_unput(int);

/*
 * Functions we use.
 */
static void newline(void);

/*
 * We have three buffers: primary, secondary, and tag buffer. The first one
 * has all data before previous start-tag, second one has data encountered
 * after previous start-tag, and the last one _has_ the start-tag.
 */
struct buffer primary_buf;
struct buffer secondary_buf;
struct buffer tag_buf;
struct buffer * current_buf;

/*
 * Indent options. To be modified only trough set_options.
 */
static char indent_char;
static int  num_indent_chars;
static bool force_newline_after_start_tag;
static bool force_newline_after_end_tag;
static bool force_newline_before_start_tag;
static bool force_newline_before_end_tag;
static bool force_always;
static int  max_columns;
static bool wrap_long_lines;
static FILE * indent_output;

/*
 * Default options.
 */
#define DEFAULT_INDENT_CHAR ' '
#define DEFAULT_NUM_INDENT_CHARS 4

/* Set default indent options.  */
void indent_options_set_defaults(struct indent_options * opts)
{
    opts->indent_char      = DEFAULT_INDENT_CHAR;
    opts->num_indent_chars = DEFAULT_NUM_INDENT_CHARS;
    opts->max_columns      = -1;
    opts->wrap_long_lines  = false;
    opts->force_newline_after_start_tag  = true;
    opts->force_newline_after_end_tag    = true;
    opts->force_newline_before_start_tag = true;
    opts->force_newline_before_end_tag   = true;
    opts->force_always                   = false;
}

/* Set indent options.  */
static void set_options(struct indent_options * opts)
{
    indent_char      = opts->indent_char;
    num_indent_chars = opts->num_indent_chars;
    max_columns      = opts->max_columns;
    wrap_long_lines  = opts->wrap_long_lines;
    force_newline_after_start_tag  = opts->force_newline_after_start_tag;
    force_newline_after_end_tag    = opts->force_newline_after_end_tag;
    force_newline_before_start_tag = opts->force_newline_before_start_tag;
    force_newline_before_end_tag   = opts->force_newline_before_end_tag;
    force_always                   = opts->force_always;
}

#define BUFFER_INITIAL_CAPACITY 1024

void indent(FILE * input, FILE * output, struct indent_options * opts)
{
    set_options(opts);

    buffer_init(&primary_buf,   BUFFER_INITIAL_CAPACITY);
    buffer_init(&secondary_buf, BUFFER_INITIAL_CAPACITY);
    buffer_init(&tag_buf,       BUFFER_INITIAL_CAPACITY);

    current_buf   = &primary_buf;
    yyin          = input;
    indent_output = output;
    yylex();

    /*
     * There might not have been a newline before EOF.
     */
    buffer_flush(current_buf, indent_output);

    buffer_release(&primary_buf);
    buffer_release(&secondary_buf);
    buffer_release(&tag_buf);
}

/* Print indent characters.  */
static void print_indent(FILE * output, int indent_level)
{
    int i;

    for (i = 0; i < (num_indent_chars * indent_level); i++) {
	fputc(indent_char, output);
    }
}

static void xml_declaration(void)
{
    buffer_push_str(current_buf, yytext);
}

static void cdata_section(void)
{
    buffer_push_str(current_buf, yytext);
}

static void doctype_declaration(void)
{
    buffer_push_str(current_buf, yytext);
}

/* XML end of line characters.  */
#define CARRIAGE_RETURN 0x0D
#define LINE_FEED       0x0A
#define NEL             0x85

static inline bool is_newline(int current)
{
    if ((CARRIAGE_RETURN == current)
	|| (LINE_FEED    == current)
	|| (NEL          == current))
	return true;

    return false;
}

/* Check for whitespace character.  */
static inline bool is_whitespace(int c)
{
    return ((c == ' ') || (c == '\f') || (c == '\t') || (c == '\v'));
}

/* Eat whitespace from stream.  */
static void eat_whitespace(void)
{
    for (;;) {
	int current = input();
	if (!is_whitespace(current)) {
	    do_unput(current);
	    break;
	}
    }
}

static int indent_level = 0;
static int indent_delta = 0;

/* Force newline before tag. Use buffer for getting current character.  */
static void force_newline_before_tag(struct buffer * buffer)
{
    int current;

    if (buffer_size(buffer) == 0) {
	/*
	 * We just did a newline, no need to force it.
	 */
	return;
    }

    current = buffer_pop_char(buffer);
    buffer_push_char(buffer, current);

    if (!is_newline(current)) {
	do_newline(buffer, "\n");
	eat_whitespace();
    }
}

/* Force newline after tag. Use lexer to get current character.  */
static void force_newline_after_tag(struct buffer * buffer)
{
    int current = input();

    do_unput(current);

    if (!is_newline(current)) {
        do_newline(buffer, "\n");
        eat_whitespace();
    }
}

static bool using_primary_buf(void)
{
    return current_buf == &primary_buf;
}

/* Merge tag and secondary buffer to primary buffer. Force newlines if
   necessary. This routine is used with start-tags.  */
static void merge_buffers_start_tag(void)
{
    if (force_newline_before_start_tag) {
        force_newline_before_tag(&primary_buf);
    }
    buffer_copy(&primary_buf, &tag_buf);
    indent_delta++;
    if (force_newline_after_start_tag) {
        force_newline_after_tag(&primary_buf);
    }
    buffer_copy(&primary_buf, &secondary_buf);

    buffer_clear(&tag_buf);
    buffer_clear(&secondary_buf);

    current_buf = &primary_buf;
}

/* Merge tag and secondary buffer back to primary buffer.  */
static void merge_buffers(void)
{
    buffer_copy(&primary_buf, &tag_buf);
    buffer_copy(&primary_buf, &secondary_buf);

    buffer_clear(&tag_buf);
    buffer_clear(&secondary_buf);

    current_buf = &primary_buf;
    /* We just processed a start-tag so bump up indent_delta.  */
    indent_delta++;
}

/* Force newline for wrapping line. Use lexer to get current character and
   do not eat whitespace from next line.  */
static void force_newline_for_wrap(struct buffer * buffer)
{
    int current = input();

    /*
     * Flush all pending stuff before doing the newline.
     */
    if (!using_primary_buf()) {
	merge_buffers();
    }
    do_newline(current_buf, "\n");

    if (!is_newline(current))
	do_unput(current);
}

static void start_tag(void)
{
    char * tmp;
    /*
     * Save text because merge_buffers_start_tag may trash it.
     */
    tmp = strdup(yytext);

    if (!using_primary_buf()) {
	/*
	 * This is second start-tag. Thus first one has children. We can force
	 * newline here if we want.
	 */
        merge_buffers_start_tag();
    }
    buffer_push_str(&tag_buf, tmp);
    current_buf = &secondary_buf;
    free(tmp);
}

static void end_tag(void)
{
    bool can_force_newline;
    char * tmp;
    /*
     * Save text because force_newline_before_tag can trash it.
     */
    tmp = strdup(yytext);

    if (using_primary_buf()) {
        can_force_newline = true;
    } else {
        /* The element didn't have any children - force newline only if user
           explicity requested that.  */
	merge_buffers();
	can_force_newline = force_always;
    }
    if (force_newline_before_end_tag && can_force_newline) {
        force_newline_before_tag(current_buf);
    }
    buffer_push_str(current_buf, tmp);
    indent_delta--;

    if (force_newline_after_end_tag && can_force_newline) {
        force_newline_after_tag(current_buf);
    }
    free(tmp);
}

static void empty_element_tag(void)
{
    bool can_force_newline;
    char * tmp;
    /*
     * Save text because force_newline_before_tag can trash it.
     */
    tmp = strdup(yytext);

    /* We treat empty element tag as a "merged" start-tag and end-tag.
       Therefore we use start-tag options before the tag and end-tag
       options after the tag.  */

    if (!using_primary_buf()) {
	/*
	 * This is second start-tag. Thus first one has children. We can force
	 * newline here if we want.
	 */
        merge_buffers_start_tag();
        can_force_newline = force_always;
    } else {
        can_force_newline = true;
    }
    buffer_push_str(current_buf, tmp);

    if (force_newline_after_end_tag && can_force_newline) {
        /* Empty element never has any children. Force newline only if user
           explicitly requested it.  */
        force_newline_after_tag(current_buf);
    }
    free(tmp);
}

static int input_and_push(void)
{
    int ret = input();
    if (ret != EOF) buffer_push_char(current_buf, ret);
    return ret;
}

static void comment(void)
{
    int c;

    buffer_push_str(current_buf, yytext);
    for (;;) {
	while ((c = input_and_push()) != '-' &&
	       c != EOF)
	    ;
	if ((c = input_and_push()) != '-') {
	    continue;
	}
	if ((c = input_and_push()) == '>') {
	    break;
	}
    }
}

static void do_newline(struct buffer * buffer, const char * text)
{
    buffer_push_str(buffer, text);

    if (indent_delta < 0) indent_level += indent_delta;
    print_indent(indent_output, indent_level);
    if (indent_delta > 0) indent_level += indent_delta;
    indent_delta = 0;

    buffer_flush(buffer, indent_output);
}

static void newline(void)
{
    /*
     * Flush all pending stuff before doing the newline.
     */
    if (!using_primary_buf()) {
	merge_buffers();
    }
    do_newline(current_buf, "\n");
    eat_whitespace();
}

/*
 * We assume tab is equal to 8 spaces.
 */
#define TAB_SIZE 8

static unsigned long indent_size(void)
{
    return (indent_char == '\t'
	    ? indent_level * TAB_SIZE
	    : indent_level * num_indent_chars);
}

static bool need_wrap(struct buffer * buffer)
{
    if (buffer == &primary_buf)
	return buffer_size(buffer) + indent_size() == max_columns;
    else
	return (buffer_size(&primary_buf) + buffer_size(&tag_buf)
		+ buffer_size(buffer) + indent_size()) >= max_columns;
}

static void content(void)
{
    char current;

    /*
     * We should get one character at a time.
     */
    int len = strlen(yytext);
    if(!len) return;
    
    current = yytext[0];
    if (current == EOF)
	return;
    
    if (is_newline(current)) {
	 newline();
	 return;
    }
    buffer_push_char(current_buf, current);

    /*
     * Forcing newline changes 'text' so lets do it after we've pushed
     * it to the buffer.
     */
    if (wrap_long_lines && need_wrap(current_buf)) {
	struct buffer tmp;
	buffer_init(&tmp, buffer_size(current_buf));
	/*
	 * Find last character that was not whitespace
	 */
	for (;;) {
	    int c;
	    if (buffer_size(current_buf) == 0)
		break;

	    c = buffer_pop_char(current_buf);
	    if (is_whitespace(c)) {
		/*
		 * Do not push whitespace because it would appear
		 * after the newline.
		 */
		break;
	    }
	    /*
	     * Characters are put in tmp buffer in reverse order.
	     */
	    buffer_push_char(&tmp, c);
	}
	force_newline_for_wrap(current_buf);
	/*
	 * Restore non-wrapped text into buffer.
	 */
	while (buffer_size(&tmp) > 0) {
	    buffer_push_char(current_buf, buffer_pop_char(&tmp));
	}
	buffer_release(&tmp);
    }
}

static void processing_insn(void)
{
    buffer_push_str(current_buf, yytext);
}
