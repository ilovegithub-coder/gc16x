#!/usr/bin/python3

import sys;
import time;

T_INS   = 0x00;
T_INT   = 0x01;
T_BYT   = 0x02;
T_LAB   = 0x03;
T_REG   = 0x04;
T_0ID   = 0x05;
T_CHR   = 0x06;
T_REG   = 0x07;
T_ADDR  = 0x08;
T_EOL   = 0x09;
T_EOF   = 0xFF;

LET    = "abcdefghijklmnopqrstuvwxyz";
DIG    = "0123456789";
WHI    = " \r\n\0";
DIGEXT = "0123456789ABCDEF";
KEY1   = ["nop"];
KEY2   = ["push", "int", "lda", "ldb", "ldc", "ldd", "lds", "ldg", "ldh", "ldl", "lodsb"];
KEYR   = ["a", "b", "c", "d", "s", "g", "h", "l", "sp", "bp"];

# Uwunny bar
def funny_bar(msg: str) -> None:
  print(f"{msg}...\033[?25l");
  for i in range(20):
    print(f"  [{'#'*i}{' '*(19-i)}]", end="\r");
    time.sleep(0.03);
  print(f"\033[?25h");

# Lexer:
def Lex(prog: str):
  prog += "\n\0";
  toks = [];
  pos = 0;
  cpos = 0;
  proglen = len(prog);
  basemode = 10;
  buf = "";
  bytesmode = 1;
  while (True):
    if (prog[pos] == "\0"):
      toks.append((T_EOL,));
      toks.append((T_EOF,));
      return toks, 0;
    elif (prog[pos] == ";"):
      pos += 1;
      while (prog[pos] != "\n"):
        pos += 1;
    elif (prog[pos] == "\""):
      pos += 1;
      while (prog[pos] != "\""):
        if (prog[pos] == "$"):
          buf += "\n";
        elif (prog[pos] == "^"):
          pos += 1;
          if (ord(prog[pos]) in range(65, 91)):
            buf += chr(ord(prog[pos])-64);
          elif (prog[pos] == "@"):
            buf += "\0";
          elif (prog[pos] == "$"):
            buf += "$";
        else:
          buf += prog[pos];
        pos += 1;
        cpos += 1;
      pos += 1;
      toks.append((T_CHR, buf, cpos));
      buf = "";
    elif (prog[pos] in WHI):
      pos += 1;
    elif (prog[pos] == "["):
      pos += 1;
      while (prog[pos] != "]"):
        buf += prog[pos];
        pos += 1;
      if (prog[pos-1] == "d"):
        toks.append((T_ADDR, int(buf[:-1], base=10)));
      elif (prog[pos-1] == "h"):
        toks.append((T_ADDR, int(buf[:-1], base=16)));
      else:
        toks.append((T_ADDR, int(buf[:-1], base=10)));
      input();
      buf = "";
      pos += 1;
    elif (prog[pos] == "\n"):
      bytesmode = 1;
      toks.append((T_EOL,));
      pos += 1;
    elif (prog[pos] in DIG):
      while (prog[pos] in DIGEXT):
        buf += prog[pos];
        pos += 1;
      if (prog[pos] == "h"):
        toks.append((T_INT, int(buf, base=16)));
      elif (prog[pos] == "d"):
        toks.append((T_INT, int(buf, base=10)));
      elif (prog[pos] == "o"):
        toks.append((T_INT, int(buf, base=8)));
      else:
        toks.append((T_INT, int(buf, base=10)));
      pos += 1;
      buf = "";
      cpos += 1+bytesmode;
    elif (prog[pos] in LET):
      while (prog[pos] in LET+DIG+"-"):
        buf += prog[pos];
        pos += 1;
      if (prog[pos] == ":"):
        toks.append((T_LAB, buf, cpos));
        pos += 1;
      else:
        if (buf in KEY2):
          toks.append((T_INS, buf, cpos));
          cpos += 2;
        elif (buf in KEYR):
          toks.append((T_REG, KEYR.index(buf), cpos));
          cpos += 1;
        elif (buf == "bytes"):
          toks.append((T_BYT, cpos));
          bytesmode = 0;
        elif (buf in KEY1):
          toks.append((T_INS, buf, cpos));
          cpos += 1;
        else:
          toks.append((T_0ID, buf));
          cpos += 2;
      buf = "";
    else:
      print(f"\033[31mUnknown\033[0m character {hex(ord(prog[pos]))[2:].upper():0>2}");
      print(f"\033[33m  Note:\033[0m at position {hex(pos)[2:]:0>4}h");
      print(f"\033[33m  Note:\033[0m at position {pos}");
      print(f"\033[33m  Note:\033[0m `{prog[pos]}`");
      return [], 1;

  return [], 1;

def FetchLabels(prog: list):
  labs = dict();
  for i in prog:
    if (i[0] == T_LAB):
      labs[i[1]] = i[2];
  return labs;

def RemEmpty(prog: str):
  return "\n".join([i for i in prog.split("\n") if i]);

# Compiler:
def CompileGC16X(prog: list, labs: dict):
  code = bytearray();
  pos = 0;
  while (prog[pos][0] != T_EOF):
    if (prog[pos][0] == T_LAB):
      pos += 1;
    elif (prog[pos][0] == T_BYT):
      pos += 1;
      while (prog[pos][0] != T_EOL):
        if (prog[pos][0] == T_INT):
          code.append(prog[pos][1] % 256);
        elif (prog[pos][0] == T_CHR):
          for i in prog[pos][1]:
            code.append(ord(i) % 256);
        else:
          print(f"  ERROR: Unknown byte {prog[pos][0]}");
          return [], 1;
        pos += 1;
      pos += 1;
    elif (prog[pos][0] == T_EOL):
      pos += 1;
    elif (prog[pos][0] == T_INS):
      if (prog[pos][1] == "push"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x0F);
          code.append(0x84);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_REG):
          code.append(0x0F);
          code.append(0x90);
          code.append(prog[pos][1] % 256);
        elif (prog[pos][0] == T_0ID):
          val = labs[prog[pos][1]];
          code.append(0x0F);
          code.append(0x84);
          code.append(val >> 8);
          code.append(val % 256);
        elif (prog[pos][0] == T_ADDR):
          code.append(0x0F);
          code.append(0x89);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        else:
          print("ERROR: `push` instruction can only take immediate values or labels");
          return 1;
        pos += 1;
      elif (prog[pos][1] == "int"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x0F);
          code.append(0xC2);
          code.append(prog[pos][1] % 256);
        elif (prog[pos][0] == T_REG):
          code.append(0x0F);
          code.append(0xC3);
          code.append(prog[pos][1] % 256);
        else:
          print("ERROR: `int` instruction can only take byte-long immediate values or registers");
          return code, 1;
        pos += 1;
      elif (prog[pos][1] == "lodsb"):
        pos += 1;
        code.append(0x10);
        code.append(0x87);
      elif (prog[pos][1] == "lda"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x66);
          code.append(0x05);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_REG):
          code.append(0x66);
          code.append(0x41);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_ADDR):
          code.append(0x66);
          code.append(0x92);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        else:
          print(f"`lda` can only take immediate words, registers, or immediate addresses");
          return code, 1;
        pos += 1;
      elif (prog[pos][1] == "ldb"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x66);
          code.append(0x06);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_REG):
          code.append(0x66);
          code.append(0x42);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_ADDR):
          code.append(0x66);
          code.append(0x93);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        else:
          print(f"`ldb` can only take immediate words, registers, or immediate addresses");
          return code, 1;
        pos += 1;
      elif (prog[pos][1] == "ldc"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x66);
          code.append(0x07);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_REG):
          code.append(0x66);
          code.append(0x43);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_ADDR):
          code.append(0x66);
          code.append(0x94);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        else:
          print(f"`ldc` can only take immediate words, registers, or immediate addresses");
          return code, 1;
        pos += 1;
      elif (prog[pos][1] == "ldd"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x66);
          code.append(0x08);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_REG):
          code.append(0x66);
          code.append(0x44);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_ADDR):
          code.append(0x66);
          code.append(0x95);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        else:
          print(f"`ldd` can only take immediate words, registers, or immediate addresses");
          return code, 1;
        pos += 1;
      elif (prog[pos][1] == "lds"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x66);
          code.append(0x09);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_REG):
          code.append(0x66);
          code.append(0x45);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_ADDR):
          code.append(0x66);
          code.append(0x96);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        else:
          print(f"`lds` can only take immediate words, registers, or immediate addresses");
          return code, 1;
        pos += 1;
      elif (prog[pos][1] == "ldg"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x66);
          code.append(0x0A);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_REG):
          code.append(0x66);
          code.append(0x46);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_ADDR):
          code.append(0x66);
          code.append(0x97);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        else:
          print(f"`ldg` can only take immediate words, registers, or immediate addresses");
          return code, 1;
        pos += 1;
      elif (prog[pos][1] == "ldh"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x66);
          code.append(0x0B);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_REG):
          code.append(0x66);
          code.append(0x47);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_ADDR):
          code.append(0x66);
          code.append(0x98);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        else:
          print(f"`ldh` can only take immediate words, registers, or immediate addresses");
          return code, 1;
        pos += 1;
      elif (prog[pos][1] == "ldl"):
        pos += 1;
        if (prog[pos][0] == T_INT):
          code.append(0x66);
          code.append(0x0C);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_REG):
          code.append(0x66);
          code.append(0x48);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        elif (prog[pos][0] == T_ADDR):
          code.append(0x66);
          code.append(0x99);
          code.append(prog[pos][1] % 256);
          code.append(prog[pos][1] >> 8);
        else:
          print(f"`ldl` can only take immediate words, registers, or immediate addresses");
          return code, 1;
        pos += 1;
      else:
        print(f"\033[31mUnknown\033[0m instruction {prog[pos][1]}");
        return code, 1;
    else:
      print(f"\033[31mUnknown\033[0m token {prog[pos]}");
      print(f"  At position {pos}");
      return code, 1;

  return code, 0;

def main(argc: int, argv: list) -> int:
  jwm = False;
  if (argc == 1):
    print("No arguments given");
    return 1;
  elif (argc == 2):
    print("No binary filename given");
    return 1;
  if (argc == 3):
    progname = argv[1];
    outname = argv[2];
  elif (argc == 4):
    if (argv[1] == "-jwm"):
      jwm = True;
    else:
      print(f"\033[31mUnknown\033[0m argument `{argv[1]}`");
      return 1;
    progname = argv[2];
    outname = argv[3];

  if (jwm): funny_bar("Loading file");
  with open(progname, "r") as fl:
    src = fl.read();
  if (jwm): funny_bar("Removing empty lines");
  src = RemEmpty(src)+"\0";
  if (jwm): funny_bar("Lexing");
  tokens, exitcode = Lex(src);
  if (jwm): funny_bar("Compiling");
  c, exitcode = CompileGC16X(tokens, FetchLabels(tokens));
  if (jwm): funny_bar("Writing to a file");
  with open(outname, "wb") as fl:
    fl.write(c);

  return 0;

sys.exit(main(len(sys.argv), sys.argv));

