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

/* Scanner for XML Indent.  */

%{
/* Flex 2.5.31 and higher limits use of unput() to definitions section
   of the input file.  */ 

static void yyunput(int, char *);

void do_unput(int c)
{
    unput(c);
}
%}

/*
 * We're mostly following the XML 1.0 specification:
 * http://www.w3.org/TR/2000/REC-xml-20001006
 */

LETTER			[[:alpha:]]
DIGIT			[[:digit:]]
NAME_CHAR		({LETTER}|{DIGIT}|\.|-|_|:)
NAME			({LETTER}|_|:)({NAME_CHAR})*
SPACE			[ \t\r\n]+

QUOTED_LITERAL		(\"[^\"]*\")|(\'[^\']*\')
SYSTEM_LITERAL		{QUOTED_LITERAL}	
PUBID_LITERAL		{QUOTED_LITERAL}
EXTERNAL_ID		("SYSTEM"{SPACE}{SYSTEM_LITERAL}|"PUBLIC"{SPACE}{PUBID_LITERAL}{SPACE}{SYSTEM_LITERAL})

XML_DECLARATION		"<?xml"[^?]*"?>"
DOCTYPE_DECLARATION	"<!DOCTYPE"{SPACE}*{NAME}({SPACE}{EXTERNAL_ID})?{SPACE}?("["([^\]]*|\][^>])*"]")?{SPACE}*">"
CDATA_SECTION		"<![CDATA["([^\]]*|\][^\]]|\]\][^>])*"]]>"
PROCESSING_INSN		"<?"([^X]|[^x])([^M]|[^m])([^L]|[^l])[^?]*"?>"

ENTITY_REF		(\&{NAME};)
CHAR_REF		((\&#[0-9]+;)|(\&#x[0-9a-fA-F]+;))
REFERENCE		({ENTITY_REF}|{CHAR_REF})
ATT_VALUE		((\"([^<\&\"]|{REFERENCE})*\")|(\'([^<\&\']|{REFERENCE})*\'))
ATTRIBUTE		{NAME}{SPACE}*"="{SPACE}*{ATT_VALUE}
START_TAG		"<"{NAME}({SPACE}*{ATTRIBUTE})*{SPACE}*">"
END_TAG			"</"{NAME}{SPACE}*">"
EMPTY_ELEMENT_TAG	"<"{NAME}({SPACE}*{ATTRIBUTE})*{SPACE}*"/>"
CONTENT			[^\<]
COMMENT			"<!--"

%%

{XML_DECLARATION} {
	xml_declaration();
}

{CDATA_SECTION} {
	cdata_section();
}

{DOCTYPE_DECLARATION} {
	doctype_declaration();
}

{START_TAG} {
	start_tag();
}

{END_TAG} {
	end_tag();
}

{EMPTY_ELEMENT_TAG} {
	empty_element_tag();
}

{CONTENT} {
	content();
}

{COMMENT} {
	comment();
}

{PROCESSING_INSN} {
	processing_insn();
}

. {
	fprintf(stderr, "Error: Scanner did not recognize string '%s'. ", yytext);
	abort();
}

%%
