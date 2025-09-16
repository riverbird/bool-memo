fpm -s dir -t deb -n boolmemo -v 0.2.0 --description "BoolHub Memo App." \
	--maintainer "Hunter Zhang <riverbird@aliyun.com>" \
	--architecture amd64 \
	-C /home/riverbird/project/bool-memo/build/linux \
	.=usr/local/bool-memo \
	bool-memo.desktop=/usr/share/applications/bool-memo.desktop
