/*
 * Copyright (C) 2002-2004  Pekka Enberg
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
#include "buffer.h"
#include "error.h"
#include "indent.h"
#include "version.h"
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void version(void)
{
    printf("XML Indent, version %s\n", VERSION);
    printf("Copyright (C) 2002-2004 Pekka Enberg\n");
}

static void usage(void)
{
    printf("Usage:  %s [options] [filename] ...\n", PACKAGE);
    printf("Options:\n");
    printf("\t-o <output>\tOutput file\n");
    printf("\t-i <indent>\tIndent level\n");
    printf("\t-t\t\tUse tabs instead of spaces for indent\n");
    printf("\t-l <max-cols>\tMaximum columns for line wrapping\n");
    printf("\t-n <pos>\tSuppress newline at position\n");
    printf("\t-f\t\tForce newline on elements without children\n");
    printf("\t-h\t\tHelp\n");
    printf("\t-v\t\tVersion information\n");
    printf("\t-w\t\tOverwrite original file\n");
}

/* Overwrite original files.  */
static bool overwrite = false;

static int format_file(const char * filename, char * output_filename,
		       struct indent_options * opts)
{
    char input_filename[FILENAME_MAX];
    FILE * input;
    FILE * output;

    input_filename[0] = '\0';

    if (filename != NULL) {
	strcpy(input_filename, filename);

        /* Avoid zero-length files.  */
	if (overwrite || strcmp(input_filename, output_filename) == 0) {
	    char backup_filename[FILENAME_MAX];
	    strcpy(backup_filename, input_filename);
	    strcat(backup_filename, "~");

	    rename(input_filename, backup_filename);
	    strcpy(output_filename, input_filename);
	    strcpy(input_filename, backup_filename);
	}
    }

    if (strlen(input_filename) > 0) {
	input = fopen(input_filename, "r");
	if (NULL == input) {
	    error("Could not open '%s': %s.", input_filename,
		  strerror(errno));
	    return EXIT_FAILURE;
	}
    } else {
	input = stdin;
    }

    if (strlen(output_filename) > 0) {
	output = fopen(output_filename, "w");
	if (NULL == output) {
	    error("Could not open '%s': %s.", output_filename,
		  strerror(errno));
	    return EXIT_FAILURE;
	}
    } else {
	output = stdout;
    }

    indent(input, output, opts);

    if (output != stdout)
    	fclose(output);

    if (input != stdout)
        fclose(input);

    return EXIT_SUCCESS;
}

static void parse_force_newline_arg(char * arg, struct indent_options * opts)
{
    if (strcmp(arg, "as") == 0) {
	opts->force_newline_after_start_tag = false;
    } else if (strcmp(arg, "ae") == 0) {
	opts->force_newline_after_end_tag = false;
    } else if (strcmp(arg, "bs") == 0) {
	opts->force_newline_before_start_tag = false;
    } else if (strcmp(arg, "be") == 0) {
	opts->force_newline_before_end_tag = false;
    }
}

static void parse_args(int argc, char * argv[], struct indent_options * opts,
		      char * output_filename)
{
    bool explicit_indent_level = false;

    for (;;) {
	int arg_index = getopt(argc, argv, "hfi:l:o:n:tvw");
	if (arg_index == -1) {
	    break;
	}
	switch (arg_index) {
        case 'h':
	    usage();
	    exit(EXIT_SUCCESS);
        case 'i':
	    opts->num_indent_chars = atoi(optarg);
	    explicit_indent_level = true;
	    break;
	case 'l':
	    opts->max_columns = atoi(optarg);
	    opts->wrap_long_lines = true;
	    break;
	case 't':
	    opts->indent_char = '\t';
	    if (!explicit_indent_level) {
		/* Default indent level for tabs is different.  */
		opts->num_indent_chars = 1;
	    }
	    break;
	case 'f':
            opts->force_always = true;
            break;
	case 'o':
	    strcpy(output_filename, optarg);
	    break;
	case 'n':
	    parse_force_newline_arg(optarg, opts);
	    break;
	case 'v':
	    version();
	    exit(EXIT_SUCCESS);
	case 'w':
	    overwrite = true;
	    break;
        default:
	    usage();
	    exit(EXIT_FAILURE);
	}
    }
}

int main(int argc, char * argv[])
{
    char output_filename[FILENAME_MAX];
    struct indent_options opts;
    int ret = EXIT_SUCCESS;
    int i;

    output_filename[0] = '\0';
    indent_options_set_defaults(&opts);

    parse_args(argc, argv, &opts, output_filename);

    /* Iterate over all input files.  */
    for (i = optind; i < argc; i++) {
        ret = format_file(argv[i], output_filename, &opts);
	if (ret != EXIT_SUCCESS)
	    break;
    }

    /* When we have no input files to process, wait for stdin.  */
    if (optind == argc)
        ret = format_file(NULL, output_filename, &opts);

    return ret;
}
