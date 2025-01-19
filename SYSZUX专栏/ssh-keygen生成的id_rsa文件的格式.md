# 背景
在Linux上我们来生成一对RSA的公钥和私钥的时候，我们通常使用下面的命令：
```bash
gemfield@gemfeld:~$ ssh-keygen 
Generating public/private rsa key pair.
Enter file in which to save the key (/home/gemfield/.ssh/id_rsa): 
Created directory '/home/gemfield/.ssh'.
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /home/gemfield/.ssh/id_rsa.
Your public key has been saved in /home/gemfield/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:/R8cHaF/fFHccc3GaPCTqHKpQxTO8mQLtx2wE+U4L3s gemfield@gemfeld.org
The key's randomart image is:
+---[RSA 2048]----+
|        +.. .. B*|
|       o B   o+.@|
|      o % o .o++ |
|       O O +  .+o|
|        S B   ..=|
|       . * . . .o|
|        + E . o  |
|         o   . . |
|              .  |
+----[SHA256]-----+
```
注意输出的内容中有这2句：
```bash
Your identification has been saved in /home/gemfield/.ssh/id_rsa.
Your public key has been saved in /home/gemfield/.ssh/id_rsa.pub

gemfield@gemfeld:~$ ls -l .ssh
total 8
-rw------- 1 gemfield gemfield 1679 Feb 23 07:34 id_rsa
-rw-r--r-- 1 gemfield gemfield  402 Feb 23 07:34 id_rsa.pub
```
其中，/home/gemfield/.ssh/id_rsa.pub就是公钥文件。而/home/gemfield/.ssh/id_rsa文件中则包含了私钥信息。你可以从上面的命令行输出中看到这两个文件的权限都不一样。

# 公钥(id_rsa.pub)
1，首先来看下公钥文件的内容：
```bash
gemfield@gemfeld:~$ cat ~/.ssh/id_rsa.pub 
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCd0w3NBkf7qoRIDoIEQslm2Ep3/kp/+U4HDgueJV8LmYSXFvk1VyLmnP8xDStoka8DNOAVFRv+1pR8sJxXlpVH+Ufy8unUBuIgZjjjd/Pt8ZRhXgAh6F0khyQLPt+rP4Wh+U/Z/ETdFsC5WSxuVND+DyZ0/Ez0b+bXolT3TMPWK8VghSoMd4vq5rC+urTLRgv5ULk9lbpmbdIGL8kKpxh0eME7EnEHpp4rkPoLjQ1ftGWJQvoDhal2dlruMsLdLq8WA4wZP6cinx8AKHFxIeBhtlAijvhBxrpr3PitNcV4FKmZcIPD6V8qrS4gguLR/a19wqulRirGlQEmFv3V2uE/ gemfield@gemfeld.org
gemfield@gemfeld:~$
```
2，公钥文件的内容由3个字段组成（使用空格分隔），其中第二个字段是公钥本身。
```bash
gemfield@gemfeld:~$ awk '{print $2}' ~/.ssh/id_rsa.pub
AAAAB3NzaC1yc2EAAAADAQABAAABAQCd0w3NBkf7qoRIDoIEQslm2Ep3/kp/+U4HDgueJV8LmYSXFvk1VyLmnP8xDStoka8DNOAVFRv+1pR8sJxXlpVH+Ufy8unUBuIgZjjjd/Pt8ZRhXgAh6F0khyQLPt+rP4Wh+U/Z/ETdFsC5WSxuVND+DyZ0/Ez0b+bXolT3TMPWK8VghSoMd4vq5rC+urTLRgv5ULk9lbpmbdIGL8kKpxh0eME7EnEHpp4rkPoLjQ1ftGWJQvoDhal2dlruMsLdLq8WA4wZP6cinx8AKHFxIeBhtlAijvhBxrpr3PitNcV4FKmZcIPD6V8qrS4gguLR/a19wqulRirGlQEmFv3V2uE/
gemfield@gemfeld:~$
```
3，id_rsa.pub文件里的公钥已经被base64编码了，gemfield先使用base64命令进行decode
```bash
gemfield@gemfeld:~$ awk '{print $2}' ~/.ssh/id_rsa.pub | base64 -d | hexdump -C
00000000  00 00 00 07 73 73 68 2d  72 73 61 00 00 00 03 01  |....ssh-rsa.....|
00000010  00 01 00 00 01 01 00 9d  d3 0d cd 06 47 fb aa 84  |............G...|
00000020  48 0e 82 04 42 c9 66 d8  4a 77 fe 4a 7f f9 4e 07  |H...B.f.Jw.J..N.|
00000030  0e 0b 9e 25 5f 0b 99 84  97 16 f9 35 57 22 e6 9c  |...%_......5W"..|
00000040  ff 31 0d 2b 68 91 af 03  34 e0 15 15 1b fe d6 94  |.1.+h...4.......|
00000050  7c b0 9c 57 96 95 47 f9  47 f2 f2 e9 d4 06 e2 20  ||..W..G.G...... |
00000060  66 38 e3 77 f3 ed f1 94  61 5e 00 21 e8 5d 24 87  |f8.w....a^.!.]$.|
00000070  24 0b 3e df ab 3f 85 a1  f9 4f d9 fc 44 dd 16 c0  |$.>..?...O..D...|
00000080  b9 59 2c 6e 54 d0 fe 0f  26 74 fc 4c f4 6f e6 d7  |.Y,nT...&t.L.o..|
00000090  a2 54 f7 4c c3 d6 2b c5  60 85 2a 0c 77 8b ea e6  |.T.L..+.`.*.w...|
000000a0  b0 be ba b4 cb 46 0b f9  50 b9 3d 95 ba 66 6d d2  |.....F..P.=..fm.|
000000b0  06 2f c9 0a a7 18 74 78  c1 3b 12 71 07 a6 9e 2b  |./....tx.;.q...+|
000000c0  90 fa 0b 8d 0d 5f b4 65  89 42 fa 03 85 a9 76 76  |....._.e.B....vv|
000000d0  5a ee 32 c2 dd 2e af 16  03 8c 19 3f a7 22 9f 1f  |Z.2........?."..|
000000e0  00 28 71 71 21 e0 61 b6  50 22 8e f8 41 c6 ba 6b  |.(qq!.a.P"..A..k|
000000f0  dc f8 ad 35 c5 78 14 a9  99 70 83 c3 e9 5f 2a ad  |...5.x...p..._*.|
00000100  2e 20 82 e2 d1 fd ad 7d  c2 ab a5 46 2a c6 95 01  |. .....}...F*...|
00000110  26 16 fd d5 da e1 3f                              |&.....?|
00000117
```
好了，现在就直观多了。

a, 前4个字节 (00 00 00 07) 说明了接下来的数据块是7个字节长，接下来的7个字节的内容就是73 73 68 2d 72 73 61, 正是字符串 "ssh-rsa" 的ASCII编码；

b, 再接下来4个字节（00 00 00 03）说明了接下来的数据块是3个字节长，接下来的4个字节的内容就是01 00 01，换算成十进制是65537,这个数字正是exponent e（参考从简单数字到现代密码学），一般来说，e都会选择65537；
```bash
gemfield@gemfeld:~$ echo "$((16#010001))"
65537
```
c, 再接下来4个字节（00 00 01 01）说明了接下来的数据快是257个字节长，这257个字节的内容是：009dd30dcd0647fbaa84480e820442c966d84a77fe4a7ff94e070e0b9e255f0b99849716f9355722e69cff310d2b6891af0334e015151bfed6947cb09c57969547f947f2f2e9d406e2206638e377f3edf194615e0021e85d2487240b3edfab3f85a1f94fd9fc44dd16c0b9592c6e54d0fe0f2674fc4cf46fe6d7a254f74cc3d62bc560852a0c778beae6b0bebab4cb460bf950b93d95ba666dd2062fc90aa7187478c13b127107a69e2b90fa0b8d0d5fb4658942fa0385a976765aee32c2dd2eaf16038c193fa7229f1f0028717121e061b650228ef841c6ba6bdcf8ad35c57814a9997083c3e95f2aad2e2082e2d1fdad7dc2aba5462ac695012616fdd5dae13f
```bash
gemfield@gemfeld:~$ N=$(awk '{print $2}' ~/.ssh/id_rsa.pub | base64 -d | hexdump -ve '1/1 "%.2x"')
gemfield@gemfeld:~$ echo ${N: -257*2}
009dd30dcd0647fbaa84480e820442c966d84a77fe4a7ff94e070e0b9e255f0b99849716f9355722e69cff310d2b6891af0334e015151bfed6947cb09c57969547f947f2f2e9d406e2206638e377f3edf194615e0021e85d2487240b3edfab3f85a1f94fd9fc44dd16c0b9592c6e54d0fe0f2674fc4cf46fe6d7a254f74cc3d62bc560852a0c778beae6b0bebab4cb460bf950b93d95ba666dd2062fc90aa7187478c13b127107a69e2b90fa0b8d0d5fb4658942fa0385a976765aee32c2dd2eaf16038c193fa7229f1f0028717121e061b650228ef841c6ba6bdcf8ad35c57814a9997083c3e95f2aad2e2082e2d1fdad7dc2aba5462ac695012616fdd5dae13f
```
这个大数字正是modulus N（参考从简单数字到现代密码学）。因为它是个有符号的数据，所以开头的00表示它是正整数，余下的256个字节说明了这个modulus N的长度有2048位，来自两个大质数p和q的乘积。这个时候，gemfield不禁回想起在本文背景中Linux console上ssh-keygen命令的输出有[RSA 2048]的字样，原来如此。

# 私钥(id_rsa）
私钥文件的内容就不能给人看了，不过gemfield这个是实验环境，就无所谓了。

id_rsa文件是base64编码的DER-encoded（Distinguished Encoding Rules，使用了 tag-length-value notation，妈呀，开发实现ss7协议的时候天天和这个玩意打交道）字符串，使用了ASN.1语法：
```bash
Version ::= INTEGER { two-prime(0), multi(1) }
      (CONSTRAINED BY
      {-- version must be multi if otherPrimeInfos present --})

  RSAPrivateKey ::= SEQUENCE {
      version           Version,
      modulus           INTEGER,  -- n
      publicExponent    INTEGER,  -- e
      privateExponent   INTEGER,  -- d
      prime1            INTEGER,  -- p
      prime2            INTEGER,  -- q
      exponent1         INTEGER,  -- d mod (p-1)
      exponent2         INTEGER,  -- d mod (q-1)
      coefficient       INTEGER,  -- (inverse of q) mod p
      otherPrimeInfos   OtherPrimeInfos OPTIONAL
  }
```
1，首先来看看私钥文件的内容：
```bash
gemfield@gemfeld:~$ cat ~/.ssh/id_rsa
-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAndMNzQZH+6qESA6CBELJZthKd/5Kf/lOBw4LniVfC5mElxb5
NVci5pz/MQ0raJGvAzTgFRUb/taUfLCcV5aVR/lH8vLp1AbiIGY443fz7fGUYV4A
IehdJIckCz7fqz+FoflP2fxE3RbAuVksblTQ/g8mdPxM9G/m16JU90zD1ivFYIUq
DHeL6uawvrq0y0YL+VC5PZW6Zm3SBi/JCqcYdHjBOxJxB6aeK5D6C40NX7RliUL6
A4WpdnZa7jLC3S6vFgOMGT+nIp8fAChxcSHgYbZQIo74Qca6a9z4rTXFeBSpmXCD
w+lfKq0uIILi0f2tfcKrpUYqxpUBJhb91drhPwIDAQABAoIBAD+nvXxBGU1vNBVg
DJ6tVVAu0rJdFS1Sn18HEjaB+jjSfYD3GiKid4guMFtXZXeysrUHYY3/SqBZaeB0
10oYiTNTXuqlgRwsfo30zOMqIW+KLX+sCz+h2dd+zlHe1RXb9AklZkiUkC3gHHFl
fx8tBHJEKA2tKVi5vZChf8WS57X8pWT+GAGjJ/Ei3PjrO5OJ8OKemhY1/91S9mMW
d45dG+/LLRgF7EuTImbhmiQi0nr2S4Xy1WiazweM0EEn9E/XVoSysUDVV2G5aHHA
E5oHtj/0ZPE7/zTYNKHi2+w1vHMJUfGkOHdw54WKoVKSIBanD6/wHmYK38tVyNkr
h79ybjECgYEAyZtjTYzn5yp+ACTrX0z905hqqrNCltlXiqmsFPBfNWmpq91GpkgF
QEyvF9Q0MFA/vflNfZwKrB25INcu/y7+J5BAN6QLAIpMmfGNpnDI071G7aoNDU4I
uSm34AhcM8ba/i+noz30xBbu5zxhSjSmKl6SYR9ZF+FKeu5L+GqE3AcCgYEAyGew
H06cu1zolkyA2ktapXuV3nTwk0XHb+RdjuySTW5vnvAdZMCfrAv0pxe3eonRATP8
7h6g96/sgCkB1SJwvI51PcfNVxncA54ITlY199UxMIAcVrKgexfTtN6r/FqYraQf
7G3ikC/gVwO1kJaILONHqseJ0y1K3wTWWm7ocwkCgYEAnEzc8w2v6Lc30nLNDCiL
jRVYdRjfIkZEKVub7uvgVG+jvHujv1yMvan2ATpib6Z3lJgILL7iQ0gT89MAO5S6
NAAQ2VJTuUp/UsZD9GryN75BlBZHYi5CcxNV29l/aiDcPT7C77sj3TaOZzWXk8k3
nheN0sBT+UCP1riSq3ghotcCgYEAxCbI+julqLXtaX8D96Yd2S83p39qIZwA8wHg
mQ3wvR1E35pCCuWG44zoL8xE6AmQqs7J1//eqdBleaOpiYWmNshw9MFluMU01c2O
b65uMF9ZQBGEq083SIQv0S7Jw7yhCARGwtFjGqHhwQl+Y0ETlGv5L60St8HzMIq5
i9ZWapECgYEAt4jizTpFET+ouSwq3iz5JG+GlB8vFrxKow9s3/fRQLUg7urptB7t
RwxwXd7fBMdyc8h+OCftiPOHpuA0SY0rVuqv5y2MFXxYcQIeRQzZ69psGbi69/Vw
6K+1DRknHOSqo8rjTUQb2Nxd38H75IkD6a6+ezvEP1740+iE5V5AzKM=
-----END RSA PRIVATE KEY-----
```
呃，我们把中间那部分base64编码的私钥信息decode出来，看看里面都包含了什么。

2，解码私钥：
```bash
gemfield@gemfeld:~$ cat ~/.ssh/id_rsa | grep -v -- '--'|  base64 -d | hexdump -C
00000000  30 82 04 a5 02 01 00 02  82 01 01 00 9d d3 0d cd  |0...............|
00000010  06 47 fb aa 84 48 0e 82  04 42 c9 66 d8 4a 77 fe  |.G...H...B.f.Jw.|
00000020  4a 7f f9 4e 07 0e 0b 9e  25 5f 0b 99 84 97 16 f9  |J..N....%_......|
00000030  35 57 22 e6 9c ff 31 0d  2b 68 91 af 03 34 e0 15  |5W"...1.+h...4..|
00000040  15 1b fe d6 94 7c b0 9c  57 96 95 47 f9 47 f2 f2  |.....|..W..G.G..|
00000050  e9 d4 06 e2 20 66 38 e3  77 f3 ed f1 94 61 5e 00  |.... f8.w....a^.|
00000060  21 e8 5d 24 87 24 0b 3e  df ab 3f 85 a1 f9 4f d9  |!.]$.$.>..?...O.|
00000070  fc 44 dd 16 c0 b9 59 2c  6e 54 d0 fe 0f 26 74 fc  |.D....Y,nT...&t.|
00000080  4c f4 6f e6 d7 a2 54 f7  4c c3 d6 2b c5 60 85 2a  |L.o...T.L..+.`.*|
00000090  0c 77 8b ea e6 b0 be ba  b4 cb 46 0b f9 50 b9 3d  |.w........F..P.=|
000000a0  95 ba 66 6d d2 06 2f c9  0a a7 18 74 78 c1 3b 12  |..fm../....tx.;.|
000000b0  71 07 a6 9e 2b 90 fa 0b  8d 0d 5f b4 65 89 42 fa  |q...+....._.e.B.|
000000c0  03 85 a9 76 76 5a ee 32  c2 dd 2e af 16 03 8c 19  |...vvZ.2........|
000000d0  3f a7 22 9f 1f 00 28 71  71 21 e0 61 b6 50 22 8e  |?."...(qq!.a.P".|
000000e0  f8 41 c6 ba 6b dc f8 ad  35 c5 78 14 a9 99 70 83  |.A..k...5.x...p.|
000000f0  c3 e9 5f 2a ad 2e 20 82  e2 d1 fd ad 7d c2 ab a5  |.._*.. .....}...|
00000100  46 2a c6 95 01 26 16 fd  d5 da e1 3f 02 03 01 00  |F*...&.....?....|
00000110  01 02 82 01 00 3f a7 bd  7c 41 19 4d 6f 34 15 60  |.....?..|A.Mo4.`|
00000120  0c 9e ad 55 50 2e d2 b2  5d 15 2d 52 9f 5f 07 12  |...UP...].-R._..|
00000130  36 81 fa 38 d2 7d 80 f7  1a 22 a2 77 88 2e 30 5b  |6..8.}...".w..0[|
00000140  57 65 77 b2 b2 b5 07 61  8d ff 4a a0 59 69 e0 74  |Wew....a..J.Yi.t|
00000150  d7 4a 18 89 33 53 5e ea  a5 81 1c 2c 7e 8d f4 cc  |.J..3S^....,~...|
00000160  e3 2a 21 6f 8a 2d 7f ac  0b 3f a1 d9 d7 7e ce 51  |.*!o.-...?...~.Q|
00000170  de d5 15 db f4 09 25 66  48 94 90 2d e0 1c 71 65  |......%fH..-..qe|
00000180  7f 1f 2d 04 72 44 28 0d  ad 29 58 b9 bd 90 a1 7f  |..-.rD(..)X.....|
00000190  c5 92 e7 b5 fc a5 64 fe  18 01 a3 27 f1 22 dc f8  |......d....'."..|
000001a0  eb 3b 93 89 f0 e2 9e 9a  16 35 ff dd 52 f6 63 16  |.;.......5..R.c.|
000001b0  77 8e 5d 1b ef cb 2d 18  05 ec 4b 93 22 66 e1 9a  |w.]...-...K."f..|
000001c0  24 22 d2 7a f6 4b 85 f2  d5 68 9a cf 07 8c d0 41  |$".z.K...h.....A|
000001d0  27 f4 4f d7 56 84 b2 b1  40 d5 57 61 b9 68 71 c0  |'.O.V...@.Wa.hq.|
000001e0  13 9a 07 b6 3f f4 64 f1  3b ff 34 d8 34 a1 e2 db  |....?.d.;.4.4...|
000001f0  ec 35 bc 73 09 51 f1 a4  38 77 70 e7 85 8a a1 52  |.5.s.Q..8wp....R|
00000200  92 20 16 a7 0f af f0 1e  66 0a df cb 55 c8 d9 2b  |. ......f...U..+|
00000210  87 bf 72 6e 31 02 81 81  00 c9 9b 63 4d 8c e7 e7  |..rn1......cM...|
00000220  2a 7e 00 24 eb 5f 4c fd  d3 98 6a aa b3 42 96 d9  |*~.$._L...j..B..|
00000230  57 8a a9 ac 14 f0 5f 35  69 a9 ab dd 46 a6 48 05  |W....._5i...F.H.|
00000240  40 4c af 17 d4 34 30 50  3f bd f9 4d 7d 9c 0a ac  |@L...40P?..M}...|
00000250  1d b9 20 d7 2e ff 2e fe  27 90 40 37 a4 0b 00 8a  |.. .....'.@7....|
00000260  4c 99 f1 8d a6 70 c8 d3  bd 46 ed aa 0d 0d 4e 08  |L....p...F....N.|
00000270  b9 29 b7 e0 08 5c 33 c6  da fe 2f a7 a3 3d f4 c4  |.)...\3.../..=..|
00000280  16 ee e7 3c 61 4a 34 a6  2a 5e 92 61 1f 59 17 e1  |...<aJ4.*^.a.Y..|
00000290  4a 7a ee 4b f8 6a 84 dc  07 02 81 81 00 c8 67 b0  |Jz.K.j........g.|
000002a0  1f 4e 9c bb 5c e8 96 4c  80 da 4b 5a a5 7b 95 de  |.N..\..L..KZ.{..|
000002b0  74 f0 93 45 c7 6f e4 5d  8e ec 92 4d 6e 6f 9e f0  |t..E.o.]...Mno..|
000002c0  1d 64 c0 9f ac 0b f4 a7  17 b7 7a 89 d1 01 33 fc  |.d........z...3.|
000002d0  ee 1e a0 f7 af ec 80 29  01 d5 22 70 bc 8e 75 3d  |.......).."p..u=|
000002e0  c7 cd 57 19 dc 03 9e 08  4e 56 35 f7 d5 31 30 80  |..W.....NV5..10.|
000002f0  1c 56 b2 a0 7b 17 d3 b4  de ab fc 5a 98 ad a4 1f  |.V..{......Z....|
00000300  ec 6d e2 90 2f e0 57 03  b5 90 96 88 2c e3 47 aa  |.m../.W.....,.G.|
00000310  c7 89 d3 2d 4a df 04 d6  5a 6e e8 73 09 02 81 81  |...-J...Zn.s....|
00000320  00 9c 4c dc f3 0d af e8  b7 37 d2 72 cd 0c 28 8b  |..L......7.r..(.|
00000330  8d 15 58 75 18 df 22 46  44 29 5b 9b ee eb e0 54  |..Xu.."FD)[....T|
00000340  6f a3 bc 7b a3 bf 5c 8c  bd a9 f6 01 3a 62 6f a6  |o..{..\.....:bo.|
00000350  77 94 98 08 2c be e2 43  48 13 f3 d3 00 3b 94 ba  |w...,..CH....;..|
00000360  34 00 10 d9 52 53 b9 4a  7f 52 c6 43 f4 6a f2 37  |4...RS.J.R.C.j.7|
00000370  be 41 94 16 47 62 2e 42  73 13 55 db d9 7f 6a 20  |.A..Gb.Bs.U...j |
00000380  dc 3d 3e c2 ef bb 23 dd  36 8e 67 35 97 93 c9 37  |.=>...#.6.g5...7|
00000390  9e 17 8d d2 c0 53 f9 40  8f d6 b8 92 ab 78 21 a2  |.....S.@.....x!.|
000003a0  d7 02 81 81 00 c4 26 c8  fa 3b a5 a8 b5 ed 69 7f  |......&..;....i.|
000003b0  03 f7 a6 1d d9 2f 37 a7  7f 6a 21 9c 00 f3 01 e0  |...../7..j!.....|
000003c0  99 0d f0 bd 1d 44 df 9a  42 0a e5 86 e3 8c e8 2f  |.....D..B....../|
000003d0  cc 44 e8 09 90 aa ce c9  d7 ff de a9 d0 65 79 a3  |.D...........ey.|
000003e0  a9 89 85 a6 36 c8 70 f4  c1 65 b8 c5 34 d5 cd 8e  |....6.p..e..4...|
000003f0  6f ae 6e 30 5f 59 40 11  84 ab 4f 37 48 84 2f d1  |o.n0_Y@...O7H./.|
00000400  2e c9 c3 bc a1 08 04 46  c2 d1 63 1a a1 e1 c1 09  |.......F..c.....|
00000410  7e 63 41 13 94 6b f9 2f  ad 12 b7 c1 f3 30 8a b9  |~cA..k./.....0..|
00000420  8b d6 56 6a 91 02 81 81  00 b7 88 e2 cd 3a 45 11  |..Vj.........:E.|
00000430  3f a8 b9 2c 2a de 2c f9  24 6f 86 94 1f 2f 16 bc  |?..,*.,.$o.../..|
00000440  4a a3 0f 6c df f7 d1 40  b5 20 ee ea e9 b4 1e ed  |J..l...@. ......|
00000450  47 0c 70 5d de df 04 c7  72 73 c8 7e 38 27 ed 88  |G.p]....rs.~8'..|
00000460  f3 87 a6 e0 34 49 8d 2b  56 ea af e7 2d 8c 15 7c  |....4I.+V...-..||
00000470  58 71 02 1e 45 0c d9 eb  da 6c 19 b8 ba f7 f5 70  |Xq..E....l.....p|
00000480  e8 af b5 0d 19 27 1c e4  aa a3 ca e3 4d 44 1b d8  |.....'......MD..|
00000490  dc 5d df c1 fb e4 89 03  e9 ae be 7b 3b c4 3f 5e  |.].........{;.?^|
000004a0  f8 d3 e8 84 e5 5e 40 cc  a3                       |.....^@..|
000004a9
```
好了，这下又直观多了：

a，第一个字节为30，这是一个SEQUENCE tag，是ASN.1 中sequence tag的值；

b，接下来是82,指明后面2个字节的长度信息是long form；

c，接下来2个字节04a5指明了整个sequence的长度，为1189个字节；也就是说04a5后面还有1189个字节的信息：
```bash
gemfield@gemfeld:~$ cat ~/.ssh/id_rsa | grep -v -- '--'|  base64 -d | hexdump -ve '1/1 "%.2x"' | wc -c
2386
gemfield@gemfeld:~$ echo $((2386/2))
1193
```
可以看到私钥信息一共是1193个字节，除去已经说过的4个字节，后面正好就是1189个字节；

d，接下来一组02 01 00，02是ASN.1 中int tag，01是长度，所以后面的1个字节00就是值，该值为0指明了RSA的版本号，意味着该版本中 RSA的私钥使用了2个质数；

e，接下来02,同理，表示int tag；接下来82表明后面是long form，该格式一味着后面2个字节是长度信息，于是接下来有01 01，说明后面是257个字节的信息，这个正是我们的modulus N；

f，modules N之后，根据本节开始部分给出的格式，后面的内容依次是：

- publicExponent e
- privateExponent d
- prime1 第一个大质数p
- prime2 第二个大质数q
- exponent1 d mod (p-1)，加密解密无用
- exponent2 d mod (q-1)，加密解密无用
- coefficient (inverse of q) mod p

其中，只有N、e、d会被直接用于加密解密，而后面的prime1、prime2、exponent1、exponent2、coefficient只是用来校验。事实上，我们可以使用openssl命令直接看这个文件的结构：
```bash
gemfield@gemfeld:~$ openssl rsa -text -noout < ~/.ssh/id_rsa
Private-Key: (2048 bit)
modulus:
    00:9d:d3:0d:cd:06:47:fb:aa:84:48:0e:82:04:42:
    c9:66:d8:4a:77:fe:4a:7f:f9:4e:07:0e:0b:9e:25:
    5f:0b:99:84:97:16:f9:35:57:22:e6:9c:ff:31:0d:
    2b:68:91:af:03:34:e0:15:15:1b:fe:d6:94:7c:b0:
    9c:57:96:95:47:f9:47:f2:f2:e9:d4:06:e2:20:66:
    38:e3:77:f3:ed:f1:94:61:5e:00:21:e8:5d:24:87:
    24:0b:3e:df:ab:3f:85:a1:f9:4f:d9:fc:44:dd:16:
    c0:b9:59:2c:6e:54:d0:fe:0f:26:74:fc:4c:f4:6f:
    e6:d7:a2:54:f7:4c:c3:d6:2b:c5:60:85:2a:0c:77:
    8b:ea:e6:b0:be:ba:b4:cb:46:0b:f9:50:b9:3d:95:
    ba:66:6d:d2:06:2f:c9:0a:a7:18:74:78:c1:3b:12:
    71:07:a6:9e:2b:90:fa:0b:8d:0d:5f:b4:65:89:42:
    fa:03:85:a9:76:76:5a:ee:32:c2:dd:2e:af:16:03:
    8c:19:3f:a7:22:9f:1f:00:28:71:71:21:e0:61:b6:
    50:22:8e:f8:41:c6:ba:6b:dc:f8:ad:35:c5:78:14:
    a9:99:70:83:c3:e9:5f:2a:ad:2e:20:82:e2:d1:fd:
    ad:7d:c2:ab:a5:46:2a:c6:95:01:26:16:fd:d5:da:
    e1:3f
publicExponent: 65537 (0x10001)
privateExponent:
    3f:a7:bd:7c:41:19:4d:6f:34:15:60:0c:9e:ad:55:
    50:2e:d2:b2:5d:15:2d:52:9f:5f:07:12:36:81:fa:
    38:d2:7d:80:f7:1a:22:a2:77:88:2e:30:5b:57:65:
    77:b2:b2:b5:07:61:8d:ff:4a:a0:59:69:e0:74:d7:
    4a:18:89:33:53:5e:ea:a5:81:1c:2c:7e:8d:f4:cc:
    e3:2a:21:6f:8a:2d:7f:ac:0b:3f:a1:d9:d7:7e:ce:
    51:de:d5:15:db:f4:09:25:66:48:94:90:2d:e0:1c:
    71:65:7f:1f:2d:04:72:44:28:0d:ad:29:58:b9:bd:
    90:a1:7f:c5:92:e7:b5:fc:a5:64:fe:18:01:a3:27:
    f1:22:dc:f8:eb:3b:93:89:f0:e2:9e:9a:16:35:ff:
    dd:52:f6:63:16:77:8e:5d:1b:ef:cb:2d:18:05:ec:
    4b:93:22:66:e1:9a:24:22:d2:7a:f6:4b:85:f2:d5:
    68:9a:cf:07:8c:d0:41:27:f4:4f:d7:56:84:b2:b1:
    40:d5:57:61:b9:68:71:c0:13:9a:07:b6:3f:f4:64:
    f1:3b:ff:34:d8:34:a1:e2:db:ec:35:bc:73:09:51:
    f1:a4:38:77:70:e7:85:8a:a1:52:92:20:16:a7:0f:
    af:f0:1e:66:0a:df:cb:55:c8:d9:2b:87:bf:72:6e:
    31
prime1:
    00:c9:9b:63:4d:8c:e7:e7:2a:7e:00:24:eb:5f:4c:
    fd:d3:98:6a:aa:b3:42:96:d9:57:8a:a9:ac:14:f0:
    5f:35:69:a9:ab:dd:46:a6:48:05:40:4c:af:17:d4:
    34:30:50:3f:bd:f9:4d:7d:9c:0a:ac:1d:b9:20:d7:
    2e:ff:2e:fe:27:90:40:37:a4:0b:00:8a:4c:99:f1:
    8d:a6:70:c8:d3:bd:46:ed:aa:0d:0d:4e:08:b9:29:
    b7:e0:08:5c:33:c6:da:fe:2f:a7:a3:3d:f4:c4:16:
    ee:e7:3c:61:4a:34:a6:2a:5e:92:61:1f:59:17:e1:
    4a:7a:ee:4b:f8:6a:84:dc:07
prime2:
    00:c8:67:b0:1f:4e:9c:bb:5c:e8:96:4c:80:da:4b:
    5a:a5:7b:95:de:74:f0:93:45:c7:6f:e4:5d:8e:ec:
    92:4d:6e:6f:9e:f0:1d:64:c0:9f:ac:0b:f4:a7:17:
    b7:7a:89:d1:01:33:fc:ee:1e:a0:f7:af:ec:80:29:
    01:d5:22:70:bc:8e:75:3d:c7:cd:57:19:dc:03:9e:
    08:4e:56:35:f7:d5:31:30:80:1c:56:b2:a0:7b:17:
    d3:b4:de:ab:fc:5a:98:ad:a4:1f:ec:6d:e2:90:2f:
    e0:57:03:b5:90:96:88:2c:e3:47:aa:c7:89:d3:2d:
    4a:df:04:d6:5a:6e:e8:73:09
exponent1:
    00:9c:4c:dc:f3:0d:af:e8:b7:37:d2:72:cd:0c:28:
    8b:8d:15:58:75:18:df:22:46:44:29:5b:9b:ee:eb:
    e0:54:6f:a3:bc:7b:a3:bf:5c:8c:bd:a9:f6:01:3a:
    62:6f:a6:77:94:98:08:2c:be:e2:43:48:13:f3:d3:
    00:3b:94:ba:34:00:10:d9:52:53:b9:4a:7f:52:c6:
    43:f4:6a:f2:37:be:41:94:16:47:62:2e:42:73:13:
    55:db:d9:7f:6a:20:dc:3d:3e:c2:ef:bb:23:dd:36:
    8e:67:35:97:93:c9:37:9e:17:8d:d2:c0:53:f9:40:
    8f:d6:b8:92:ab:78:21:a2:d7
exponent2:
    00:c4:26:c8:fa:3b:a5:a8:b5:ed:69:7f:03:f7:a6:
    1d:d9:2f:37:a7:7f:6a:21:9c:00:f3:01:e0:99:0d:
    f0:bd:1d:44:df:9a:42:0a:e5:86:e3:8c:e8:2f:cc:
    44:e8:09:90:aa:ce:c9:d7:ff:de:a9:d0:65:79:a3:
    a9:89:85:a6:36:c8:70:f4:c1:65:b8:c5:34:d5:cd:
    8e:6f:ae:6e:30:5f:59:40:11:84:ab:4f:37:48:84:
    2f:d1:2e:c9:c3:bc:a1:08:04:46:c2:d1:63:1a:a1:
    e1:c1:09:7e:63:41:13:94:6b:f9:2f:ad:12:b7:c1:
    f3:30:8a:b9:8b:d6:56:6a:91
coefficient:
    00:b7:88:e2:cd:3a:45:11:3f:a8:b9:2c:2a:de:2c:
    f9:24:6f:86:94:1f:2f:16:bc:4a:a3:0f:6c:df:f7:
    d1:40:b5:20:ee:ea:e9:b4:1e:ed:47:0c:70:5d:de:
    df:04:c7:72:73:c8:7e:38:27:ed:88:f3:87:a6:e0:
    34:49:8d:2b:56:ea:af:e7:2d:8c:15:7c:58:71:02:
    1e:45:0c:d9:eb:da:6c:19:b8:ba:f7:f5:70:e8:af:
    b5:0d:19:27:1c:e4:aa:a3:ca:e3:4d:44:1b:d8:dc:
    5d:df:c1:fb:e4:89:03:e9:ae:be:7b:3b:c4:3f:5e:
    f8:d3:e8:84:e5:5e:40:cc:a3
```
# 最后
这个星球上使用最多的加密算法，就是仰仗于大质数很难分解，真是神奇的数学！
