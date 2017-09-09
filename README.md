# A super simple radiko "タイムフリー" downloader
radikoのタイムフリーをダウンロードするシンプルなスクリプトです。

## Prerequisites
1. このプログラムはPython 3によって書かれています。Python 3をインストールし、必要なライブラリをインストールしてください:
···bash
$ pip install -r requirements.txt
···
2. このプログラムは[PhantomJS](http://phantomjs.org/)を使用しています。PhantomJSの最新のバイナリファイルを[ここ](http://phantomjs.org/download.html)からダウンロードし、プロジェクトのディレクトリに配置してください。
3. [ffmpeg](https://www.ffmpeg.org/)と[swftools](http://www.swftools.org/)をインストールしてください。Macの場合はHomebrewによりインストールが可能です:
···bash
$ brew install ffmpeg
$ brew install swftools
···

## Usage
[radiko.jp](http://radiko.jp/)の[タイムフリー](http://radiko.jp/#!/timeshift)のページからダウンロードしたい番組を表示し、URLをコピーします。そしてターミナルから、次のようにプログラムを起動してください:
···bash
$ python radiko.py 'http://radiko.jp/#!/ts/<station_id>/<ft>'
···
`<station_id>`にはアルファベットの大文字やハイフンが、また`<ft>`には数字がそれぞれ含まれているはずです。URLをシングルクオート（`'`）で囲むことを忘れないようにしてください。