----------------------------------------------------------------

  While言語のインタプリタ

      佐藤伸也 作（2021年2月6日版）
      shinya.sato.mito@vc.ibaraki.ac.jp

----------------------------------------------------------------

1. whileプログラムのインタプリタ

書籍「チューリングの考えるキカイ ～人工知能の父に学ぶコンピュータ・サイエンスの基礎」
（阿部彩芽・笠井琢美 著、技術評論社）で導入されている whileプログラムのインタプリタです。
なお、このプログラムは書籍のファンである作者が勝手に作成したものであり、
書籍の著者ら、出版社とはなんの関係もありません。

書籍のサイト：https://gihyo.jp/book/2018/978-4-7741-9689-3


1-1. 必要環境

Windows 10(64bit)版のバイナリは、Windows10フォルダ内の exeファイルを使ってください。

プログラムのソースは source フォルダに入っています。
実行には、Python とライブラリ PLY(Python Lex-Yacc) が必要です。
動作確認は以下の環境で行っています。

- Windows 10(64bit), Python 3.7.7 （Python3 はもっと低いバージョンでも動くと思います）


1-2. ライセンス

このディレクトリに含まれるソースコードは
すべて佐藤伸也が著作権を保持し、MITライセンスのもとで配布します。
コピー、配布、変更、再配布、商用利用など、ご自由に使ってください。
このソフトウェアにはなんの保証もついてきませんので、
利用したことで何か問題が起きたとしても作者はなんの責任も負いません。

佐藤伸也 / Shinya Sato


----------------------------------------------
2. 使い方

インタプリタが起動すると、プログラムが入力できるウィンドウ（コマンドプロンプト）が表示されます。
画面左に表示される 「[0] $」は「プロンプト（prompt）」と呼ばれ、
プログラムが入力できることを意味しています
（カギかっこ内の数字は、何行目の入力なのかを示しています）。

プログラムの実行は Enterキーを押してください。
例えば、「[0] $」と表示されている左側に 「x0 := 23」と入力して
（半角スペースは無くても結構です）Enterキーを押すと、
変数 x0 に 23 が代入されます（例1）。

--- 例1 -----------
[1] $ x0 := 23
[2] $
------------------


変数 x0 の値を表示させるときには print文を使って「print(x0)」と
入力して実行してください（例2）。

--- 例2 -----------
[2] $ print(x0)
      23

[3] $
------------------

print に複数の変数名をカンマ「,」で区切って指定すると、
複数の変数の値が表示できます（例3）：

--- 例3 -----------
[3] $ x1:=100
[4] $ print(x0,x1)
      23 100

[5] $
------------------


一つの変数の値だけを表示させたいときには、その変数を入力して実行してください（例4）：

--- 例4 -----------
[6] $ x0
      23

[7] $
------------------



----------------------------------------------
3. 書籍のプログラム表記との違い

- 演算子にはすべて半角記号を使います：
  - 代入記号は「←」の代わりに「:=」を使います。
  - 「≠」には 「!=」 を使います。 
  - 「＞」には 「>」 を使います。
  - 「≧」には 「>=」 を使います。
  - 「＜」には 「<」 を使います。
  - 「≦」には 「<=」 を使います。

- 四則演算には +, -, *, div が使えます
（組み込み演算として実装しています）。
また、割り算の余りには mod が使えます。

- 行中の # から右のものはコメントとして扱われ、
プログラムとしては解釈されません。

- 配列には鍵かっこを使います。例えば、3,6,8 を要素とする配列は
  [3,6,8]
  と書きます。
  
- 文字、文字列は「"」で囲みます。例えば、文字列 hello は
  "hello"
と書きます。文字列の同一性は「=」を用いて判定できます。
今のところ、文字列に対しても操作は、それ以外にはありません
（文字列を部分的に取得したり、長さを取得するような組み込み関数はありません）。


- whileプログラムの文として「空文」を認めています。そのため、複合文
  「begin s1;s2; ... ;sm end」
  を、
  「begin s1;s2; ... ;sm; end」
として書けます
（つまり、最後の文 sm にセミコロンを付けてもエラーになりません）。
  

----------------------------------------------
4. プログラムのサンプル

## 引数の値を一つ増やす
procedure z:= oneUp(a): begin
  b:=a;
  b++;
  z:=b;
end

# 実行例
x:=100
z:=oneUp(x)
print(z) # 101 が表示される
print(x) # 100 が表示される

# ちなみに、procedure は式として扱われるようにしてあるので
# oneUp(200) として実行すると 201 が返ってくる
oneUp(200)


## 素数判定
procedure  z:= isPrime(n): begin
  z:=1;
  w:=2;
  while (w < n) and (z = 1) do begin
    if (n mod w)=0 then z:=0;
    w++;
  end;
end

# 実行例
z:=isPrime(3)
print(z) # 1 が表示される
z:=isPrime(4)
print(z) # 0 が表示される



## n番目の素数を求める
procedure  z:= getPrime(n): begin
  hit:=0;
  z  :=2;
  while (hit < n) do begin
    z++;
    hantei := isPrime(z);
    if hantei then hit++;
  end;
  #print(z);
end

# 実行例
z:=getPrime(5)
print(z) # 13 が表示される


## チューリングマシン（単能）
命令表
|条件 |     |      | 動作 |     |
|---  | --- | ---  | ---  | --- |
|q0   | 1   | →   | q1   | ␣  |
|q1   | ␣  | →   | q2   | 右  |
|q2   | 1   | →   | q1   | ␣  |

テープの初期状態
|▷ | 1 | 1 | 1 |

ヘッド位置:1（「▷」のところ）

ヘッドの内部状態:q0


# プログラム開始
x0 :=["▷", "1", "1", "1"]
h := 1
q := 0

begin
  active := 1;
  while (active = 1) do begin
    print(x0,h,q);
    kigou := x0[h];
    if (q = 0) and (kigou = "1") then begin
      q :=1;  x0[h] := "␣" end
    else if (q = 1) and (kigou = "␣") then begin
      q := 2;  h++  end
    else if (q = 2) and (kigou = "1") then begin
      q := 1;  x0[h] := "␣" end
    else  active := 0
  end
end


# 実行例
# ["▷", "1", "1", "1"] 1 0
# ["▷", "␣", "1", "1"] 1 1
# ["▷", "␣", "1", "1"] 2 2
# ["▷", "␣", "␣", "1"] 2 1
# ["▷", "␣", "␣", "1"] 3 2
# ["▷", "␣", "␣", "␣"] 3 1
# ["▷", "␣", "␣", "␣"] 4 2
```


## 階乗

# 再帰関数の例です
procedure z:=fact(n): begin
  if n=0 then begin
    z:=1
  end
  else begin
       z1 := fact(n-1);
       z := n * z1;
  end
end

# 実行例
z:=fact(3)
print(z)   # 6のはず


## 階乗（スタックによる再帰除去版）

### スタック構造
procedure z:=mkStack(): begin
  z:=[0,[0]]
end

procedure z:=isEmpty(s): begin
  if s[0]=0 then z:=1
  else z:=0
end

procedure z:=push(s,n): begin
  index := s[0];
  index++;
  vals := s[1];
  vals[index] := n;
  z := [index, vals];
end

procedure z:=pop(s): begin
  index := s[0];
  index--;
  z := [index, s[1]]
end

procedure z:=top(s): begin
  index := s[0]; 
  vals := s[1];
  z := vals[index] 
end


# 実行例
stack := mkStack()
print(stack)  # [0, [0]]

stack := push(stack, 100)
print(stack)  # [1, [0, 100]]

stack := push(stack, 38)
print(stack)  # [2, [0, 100, 38]]

z:=top(stack)
print(z)  # 38

stack := pop(stack)
print(stack)  #  [1, [0, 100, 38]]  
     # 38 が残るが、参照先を示す stack[1] が 2 から 1 になっているので
     # スタック構造としては正しく機能できる

z:=top(stack)
print(z)  # 100  （このように、現在のトップに積まれている値が取得できる）

z:=isEmpty(stack)
print(z)  # 0

stack := pop(stack)
z:=isEmpty(stack)
print(z)  # 1
print(stack)  # [0, [0, 100, 38]] （ごみは残るが index が 0 であるため empty）


### 階乗（再帰なし）
procedure z:=Fact(n): begin
  task := mkStack();
  retval := mkStack();
  task := push(task, [1, n]);
  sentinel := 0;
  
  while sentinel=0 do begin 
    aTask := top(task);  
    task := pop(task);
    n := aTask[1];
    if aTask[0]=1 then begin
      if n=0 then 
        retval := push(retval, 1)
      else begin
        task := push(task, [2, n]);
        task := push(task, [1, n-1]);
      end
    end
    else begin
      z1 := top(retval);  retval := pop(retval);
      z := n * z1;
      retval := push(retval, z);
    end;

    sentinel := isEmpty(task);
  end;
  z := top(retval)
end


# 実行例
z:=Fact(4)
print(z)  # 24 となるはず


## whileプログラムのインタプリタ eval（再帰的定義版）

#なお、与えるプログラムはあらかじめ構文木に変換しておく
# xi++ => ["incx", i]
# xi-- => ["decx", i]
# begin s1;...;sn end => ["multi", n, [s1,...,sn]]
# while xi != 0 do s  => ["while", i, s]

procedure z:=eval(s, env): begin
  if s[0] = "incx" then begin
    index := s[1];
    env[index] := env[index]+1
  end
  else if s[0] = "decx" then begin
    index := s[1];
    env[index] := env[index]-1
  end
  else if s[0] = "multi" then begin
    length := s[1];
    multis := s[2];
    i := 0;
    while i<length do begin
      env := eval(multis[i], env);
      i++;
    end;
  end
  else begin
    cond_index := s[1];
    sentence := s[2];
    while env[cond_index] != 0 do begin
      env := eval(sentence, env);
    end;
  end;
  z:=env
end


# 実行例
# P  : x0++
# x0 : 10
# とする。

Env := [10]
print(Env)
Env := eval(["incx", 0], Env)
print(Env)  # [11] となるはず



# 実行例
# P  : while x1 != 0 do begin x1--; x0++; x0++ end
# x0 : 0
# x1 : 10
# とする。

Env := [0,10]
print(Env)
Env := eval(["while", 1, ["multi", 3, [["decx", 1], ["incx", 0], ["incx", 0]]]], Env)
print(Env)  # [20,0] となるはず










----------------------------------------------
5. 変更履歴
2021-02-06
結果出力のインデントが、9行目にも関わらず
10行目のものとなっていたので修正した。



2021-02-05
eval_sentence を再帰版に戻した。
また、procedure の呼び出しを「文」ではなく「式」として扱うようにした。



2021-01-25
While言語のインタプリタ eval（再帰的定義版）の例を
少しだけ複雑にした。


2021-01-14
print文にて文字列の表示が行えなかったので修正した。


2020-12-20
配布版に含まれている不要なライブラリを削除した。


2020-01-20
配列の表示を Python dic形式から
[a,b,c] 形式に変更した
（pretty_print_val が担当）。
[今後の課題]
・手続き呼び出しの入れ子を許可するようにする。


2020-01-18
文を解釈する eval_sentence() から
再帰呼び出しを除去した。
これは、テキストの万能プログラム U から
再帰呼び出しを除去する方法のチェックも兼ねている。
[今後の課題]
・配列の表示を [a,b,c] にする。
・手続き呼び出しの入れ子を許可するようにする。


2019-11-25
procedure の呼出し処理におけるローカル変数の保存を
stack で行うことにした
今後の課題：
配列の表示を [a,b,c] にする。
配列に対しての組み込み関数 len, reverse, push, pop を用意する。


2018-11-02
配列、文字列を追加
IF-THEN-ELSE が解釈されないバグを解消






以上
----------------------------------------------------------------
