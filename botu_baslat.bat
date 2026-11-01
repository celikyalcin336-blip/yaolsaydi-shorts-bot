@echo off
chcp 65001 > nul
title Ya Olsaydi Telegram Bot Dinleyicisi
echo ========================================================
echo   YA OLSAYDI? TELEGRAM CANLI KOMUT DİNLEYİCİSİ
echo ========================================================
echo.
echo Telegram'dan /video_uret komutunu bekliyor...
echo.

python telegram_bot_listener.py

pause
