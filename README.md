# whileプログラムのインタプリタ

![screen-shot](https://github.com/shinnya-sato/while-interpreter/blob/main/pic/screen_shot1.png)

書籍「チューリングの考えるキカイ ～人工知能の父に学ぶコンピュータ・サイエンスの基礎」
（阿部彩芽・笠井琢美 著、技術評論社）で導入されている whileプログラムのインタプリタです。
なお、このインタプリタは書籍のファンである作者が勝手に作成したものであり、
書籍の著者ら、出版社とはなんの関係もありません。

書籍のサイト：https://gihyo.jp/book/2018/978-4-7741-9689-3


## 必要環境

Windows10(64bit)版のバイナリ while-v1.0-release-Win10-64bit.exe は、右側の「Rereases」 v1.0 のリリース（または下記リンク）から入手できます：
https://github.com/shinnya-sato/while-interpreter/releases/download/v1.0-release/while-v1.0-release-Win10-64bit.exe

プログラムのソースは source フォルダに入っています。
ソースの実行には Python とライブラリ PySide2、 PLY(Python Lex-Yacc) が必要です。
動作確認は以下の環境で行っています。

- Windows 10(64bit), Python 3.7.7 （Python3 はもっと低いバージョンでも動くと思います）


## ライセンス

このディレクトリに含まれるソースコードは
佐藤伸也が著作権を保持し、MITライセンスのもとで配布します。
コピー、配布、変更、再配布、商用利用など、ご自由に使ってください。
このソフトウェアにはなんの保証もついてきませんので、
利用したことで何か問題が起きたとしても作者はなんの責任も負いません。

佐藤伸也 / Shinya Sato


# 使い方

アプリの画面には2つのテキストアリアがあります：
- 背景が白い方にプログラムを入力します。
- 灰色のものには実行結果が表示されます。

背景が白い方にプログラム ```print(23)``` を入力し、
画面右側にある「実行」ボタンを押してみましょう。

![screen-shot2](https://github.com/shinnya-sato/while-interpreter/blob/main/pic/screen_shot2.png)

実行結果のところに ```23``` と表示されます。

![screen-shot3](https://github.com/shinnya-sato/while-interpreter/blob/main/pic/screen_shot3.png)

なお、正しく入力されていないときにはエラーが表示されますので、
訂正してもう一度「実行」ボタンを押してください。

複数の文を実行するときには複合文 begin ～ end を使います。
例えば、変数 ```x0``` に ```23+10``` の結果を代入し、``x0`` の値を表示するには
例1のようにプログラムを入力して実行します（```33```と表示されるはずです）。

例1
```
begin
  x0:=23+10;
  print(x0);
end
```

行頭の半角スペースは無くても結構ですが、
begin ～ end で囲まれていることが分かりやすいように
インデントとして半角スペースを 2文字（程度）入れておくと良いです
（Tabキーを使っても良いです）。

print文で複数の変数の値を表示したいときには、
カンマ ```,``` で区切って変数名を指定してください（例2）：


例2
```
begin
  x0:=23;
  x1:=x0+10;
  print(x0,x1);
end
```


※実行は、「実行」ボタンを押す代わりに
キーボードショートカット Ctrl+Enter でも行えます。


# 書籍のプログラム表記との違い

- 演算子にはすべて半角記号を使います：
  - 代入記号は「←」の代わりに ```:=``` を使います。
  - 「≠」には ```!=``` を使います。 
  - 「＞」には ```>``` を使います。
  - 「≧」には ```>=``` を使います。
  - 「＜」には ```<``` を使います。
  - 「≦」には ```<=``` を使います。

- 四則演算には ```+```, ```-```, ```*```, ```div``` が使えます
（組み込み演算として実装しています）。また、割り算の余りには
 ```mod``` が使えます。

- 行中の # から右のものはコメントとして扱われ、プログラムとしては解釈されません。

- 配列には鍵かっこを使います。例えば、3,6,8 を要素とする配列は
  ```[3,6,8]```
  と書きます。
  
- 文字、文字列は「"」で囲みます。例えば、文字列 hello は ```"hello"```
と書きます。文字列の同一性は ```=```を用いて判定できます。
今のところ、文字列に対しても操作は、それ以外にはありません
（文字列を部分的に取得したり、長さを取得するような組み込み関数はありません）。


- whileプログラムの文として「空文」を認めています。そのため、複合文
```begin s1;s2; ... ;sm end```
を、
```begin s1;s2; ... ;sm; end```
として書けます（つまり、最後の文 sm にセミコロンを付けてもエラーになりません）。
  
- whileプログラムの文は 1行で書いてください。なお、begin ～ end の間は、改行しても1行の文として解釈されます。


# プログラムのサンプル

## 引数の値を一つ増やす
```
# プログラム開始
procedure z:= oneUp(a): begin
  b:=a;
  b++;
  z:=b;
end

# 実行例
begin
  x:=100;
  z:=oneUp(x);
  print(z);   # 101 が表示されるはず
  print(x);   # 100 が表示されるはず

  # ちなみに、procedure は式として扱われるようにしてあるので
  # oneUp(200) として実行すると 201 が返ってくる
  print(oneUp(200))
end
```


## 素数判定
```
# プログラム開始
procedure  z:= isPrime(n): begin
  z:=1;
  w:=2;
  while (w < n) and (z=1) do begin
    if (n mod w)=0 then z:=0;
    w++;
  end
end

# 実行例
begin
  z:=isPrime(3);
  print(z);       # 1 が表示されるはず
  z:=isPrime(4);
  print(z)        # 0 が表示されるはず
end
```



## n番目の素数を求める
```
# プログラム開始
procedure  z:= isPrime(n): begin
  z:=1;
  w:=2;
  while (w < n) and (z=1) do begin
    if (n mod w)=0 then z:=0;
    w++;
  end
end

procedure  z:= getPrime(n): begin
  hit:=0;
  z:=2;
  while (hit < n) do begin
    z++;
    kekka:=isPrime(z);
    if kekka=1 then hit++;
  end;
  #print(z);
end

# 実行例
begin
  z:=getPrime(5);
  print(z);       # 13 が表示されるはず
end
```


## チューリングマシン（単能）
命令表
|条件 |     |      | 動作 |     |
|---  | --- | ---  | ---  | --- |
|q0   | 1   | →   | q1   | ␣  |
|q1   | ␣  | →   | q2   | 右  |
|q2   | 1   | →   | q1   | ␣  |

テープの初期状態
|▷|1|1|1|
| --- | --- | --- | --- | 

ヘッド位置:1（「▷」のところ）

ヘッドの内部状態:q0

```
# プログラム開始
begin
  # 初期状態の設定
  x0:=["▷", "1", "1", "1"];
  h:=1;
  q:=0;

  # 実行開始
  active:=1;
  while (active=1) do begin
    print(x0, h, q);
    kigou := x0[h];

    if (q=0) and (kigou="1") then begin
      q:=1;  x0[h] := "␣" 
    end
    else if (q=1) and (kigou="␣") then begin
      q:=2;  h++ 
    end
    else if (q=2) and (kigou="1") then begin
      q:=1;  x0[h]:="␣" 
    end
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


## 階乗（再帰関数の例です）

```
# プログラム開始
procedure z:=fact(n): begin
  if n=0 then begin
    z:=1
  end
  else begin
       z1:=fact(n-1);
       z := n*z1;
  end
end

# 実行例
begin
  z:=fact(3);
  print(z)      # 6のはず
end
```


## スタック
```
# プログラム開始
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
begin
  stack := mkStack();
  print(stack);  # [0, [0]]

  stack := push(stack, 100);
  print(stack);  # [1, [0, 100]]

  stack := push(stack, 38);
  print(stack);  # [2, [0, 100, 38]]

  z:=top(stack);
  print(z);  # 38

  stack := pop(stack);
  print(stack);  #  [1, [0, 100, 38]]  
     # 38 が残るが、参照先を示す stack[1] が 2 から 1 になっているので
     # スタック構造としては正しく機能できる

  z:=top(stack);
  print(z);  # 100  （このように、現在のトップに積まれている値が取得できる）

  z:=isEmpty(stack);
  print(z);  # 0

  stack := pop(stack);
  z:=isEmpty(stack);
  print(z);      # 1
  print(stack);  # [0, [0, 100, 38]] （ごみは残るが index が 0 であるため empty）
end
```



## 階乗（スタックを用いた再帰なし版）

```
# プログラム開始
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


# 再帰なしの階乗
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
begin
  z:=Fact(4);
  print(z)     # 24 になるはず
end
```




## whileプログラムのインタプリタ eval（再帰的定義版）

```
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
begin

  # 初期条件
  # P  : x0++
  # x0 : 10

  Env := [10];
  print(Env);
  Env := eval(["incx", 0], Env);
  print(Env);  # [11] になるはず


  # 初期条件
  # P  : while x1 != 0 do begin x1--; x0++; x0++ end
  # x0 : 0
  # x1 : 10

  Env := [0,10];
  print(Env);
  Env := eval(["while", 1, ["multi", 3, [["decx", 1], ["incx", 0], ["incx", 0]]]], Env);
  print(Env);  # [20,0] になるはず
end
```
