
rubika.ir
بات روبیکا
6–7 minutes
معرفی

روبیکا مجموعه‌ای از APIها را در اختیار توسعه‌دهندگان قرار می‌دهد که با استفاده از آن‌ها می‌توان بات ایجاد و مدیریت کرد. برای استفاده از این APIها، مراحل زیر را دنبال کنید.
مراحل استفاده¶

    ۱. با استفاده از BotFather به آدرس BotFather@ در روبیکا، یک بات ایجاد کنید.
    ۲. توکن دریافتی را ذخیره کرده و در مراحل بعدی از آن استفاده کنید.
    ۳. با استفاده از توکن مرحله‌ی قبل و متد مورد نظر، یک URL با قالب زیر ایجاد کرده و درخواست خود را با متد POST ارسال کنید.

https://botapi.rubika.ir/v3/{token}/{method}

توضیحات¶

پس از ساخت بات در BotFather، برای اینکه بات شما از اقدامات کاربران (ارسال پیام، کلیک روی دکمه‌ها و …) مطلع شود، دو روش اصلی وجود دارد:

(Long Polling)

در این روش، بات شما به‌صورت دوره‌ای از سرور روبیکا بررسی می‌کند که آیا رویداد یا پیام جدیدی دریافت شده است یا خیر.

برای پیاده‌سازی، باید در بازه‌های زمانی مشخص (برای مثال هر ۵ ثانیه) و با استفاده از مقدار start_id که از فراخوانی قبلی دریافت کرده‌اید، متد getUpdates را صدا بزنید.

در این روش ممکن است از رویدادها با تأخیر مطلع شوید، زیرا تا زمانی که درخواست جدیدی ارسال نکنید، پیام‌ها دریافت نمی‌شوند و به همان میزان نیز پاسخ بات به کاربر با تأخیر همراه خواهد بود.

روش ۲: دریافت اطلاعات از طریق تعریف Endpoint

(Webhook)

در این روش، با تنظیم یک Endpoint روی سرور خود، به‌محض وقوع هر رویداد مرتبط با بات (مانند ارسال پیام یا کلیک روی دکمه)، روبیکا اطلاعات رویداد را به آدرسی که مشخص کرده‌اید ارسال می‌کند.

برای فعال‌سازی این روش، با استفاده از متدی مانند updateBotEndpoint، آدرس سرور خود را به پلتفرم معرفی می‌کنید. پس از تنظیم Endpoint، در هر رویداد، هر زمان کاربر پیامی ارسال کند، پلتفرم یک درخواست POST شامل اطلاعات رویداد را (بر اساس نوع آن) در قالب‌هایی مانند Update، InlineMessage و … به Endpoint شما ارسال خواهد کرد.

توجه:

این روش نیازمند یک سرور با دامنه عمومی و پشتیبانی از SSL (HTTPS) است، زیرا پلتفرم تنها به آدرس‌های امن متصل می‌شود.

در صورت بروز خطا یا عدم دریافت پاسخ معتبر از Endpoint، امکان توقف موقت ارسال رویدادها توسط پلتفرم وجود دارد.

برای انواع مختلف رویدادها، لازم است Endpointهای مجزایی تعریف شود که مهم‌ترین آن‌ها در ادامه معرفی شده‌اند.
receiveUpdate¶

هر زمان کاربر پیامی ارسال کند یا دکمه‌های ChatKeypad (دکمه‌های پایین صفحه چت) را لمس کند، شما یک درخواست POST دریافت می‌کنید که بدنه آن شامل شیء Update است.


نمونه body :

{
  "update": {
      "type": "NewMessage",
      "chat_id": "{chat_id}",
      "new_message": {
          "message_id": "{message_id}",
          "text": "custom text",
          "time": "1643122902",
          "is_edited": false,
          "sender_type": "User",
          "sender_id": "{sender_id}",
          "aux_data": {
              "start_id": null,
              "button_id": "{button_id}"
          }
      }
  }
}

receiveInlineMessage¶

هرگاه کاربر روی InlineKeypad (دکمه‌های شیشه‌ای زیر پیام‌ها) کلیک کند، یک درخواست POST دریافت می‌کنید که بدنه‌ی آن شامل شیء POST دریافت می‌کنید که بدنه (body) آن شامل شیء InlineMessage است.


نمونه body :

{
    "inline_message": {
        "sender_id": "{sender_id}",
        "text": "custom text",
        "location": null,
        "aux_data": {
            "start_id": null,
            "button_id": "{button_id}"
        },
        "message_id": "{message_id}",
        "chat_id": "{chat_id}"
    }
}

به‌طور کلی، انتخاب بین دو روش دریافت رویداد به شرایط زیر بستگی دارد:

    روش getUpdates

    مناسب برای پروژه‌های ساده، محیط‌های توسعه یا زمانی که امکان راه‌اندازی سرور عمومی و HTTPS وجود ندارد. این روش پیاده‌سازی ساده‌تری دارد، اما به‌دلیل ماهیت دوره‌ای درخواست‌ها، دریافت رویدادها با تأخیر همراه است.
    روش تعریف Endpoint

    مناسب برای پروژه‌های پایدار و در مقیاس productionاست. در این روش، رویدادها به‌صورت آنی و بدون تأخیر به سرور شما ارسال می‌شوند. استفاده از این روش مستلزم داشتن سرور با دامنه عمومی و پشتیبانی از SSL است.

در محیط‌های عملیاتی، استفاده از Webhook به‌دلیل کارایی بالاتر و دریافت بلافاصله رویدادها توصیه می‌شود.

زمانی که شما از طرف بات به شکل بالا Request را دریافت و پردازش کردید، می‌توانید با استفاده از این متد‌ها به آن پاسخ دهید.




rubika.ir
متد ها - بات روبیکا
78–100 minutes
متد ها
دریافت اطلاعات بات¶

    متد: getMe
    اطلاعات پایه‌ای بات را بازمی‌گرداند، شامل نام، نام کاربری، شناسه و... تا بتوان هویت و تنظیمات اولیه بات را بررسی کرد.
    ورودی
    این متد اطلاعات پایه‌ای بات را برمی‌گرداند. معمولاً برای تست اتصال بات و شناسایی آن استفاده می‌شود و هیچ پارامتری به عنوان ورودی دریافت نمیکند.
    خروجی

فیلد 	نوع 	توضیحات
bot 	Bot 	بات

    مثال

    cURLPythonNodeJs

    curl -X POST https://botapi.rubika.ir/v3/{token}/getMe

    import requests

    url = f'https://botapi.rubika.ir/v3/{token}/getMe'

    response = requests.post(url)

    print(response.text)

    from rubika_bot.requests import get_me
    from rubika_bot.models import Bot

    bot: Bot = get_me(token='SUPER_SECRET_TOKEN')

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/getMe',
      'headers': {
      }
    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ارسال پیام (Text, Keypad, InlineKeypad)¶

    متد: sendMessage
    این متد پیام را از بات به یک چت ارسال می‌کند و نوع محتوا را می‌توان مشخص کرد. مانند ارسال Text، Keypad یا InlineKeypad برای دریافت پاسخ مستقیم کاربر.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
text 	string 	متن پیام
chat_keypad 	Keypad 	keypad
disable_notification 	bool 	مشخص می‌کند آیا اعلان‌ها غیرفعال شوند یا خیر (پیش‌فرض: false)
inline_keypad 	Keypad 	Keypad
reply_to_message_id 	string 	شناسه پیام برای ریپلای
chat_keypad_type 	ChatKeypadTypeEnum 	نوع keypad

    خروجی

فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/sendMessage' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "text": "Welcome",
                "inline_keypad": {
                    "rows": [
                        {
                            "buttons": [
                                {
                                    "id": "100",
                                    "type": "Simple",
                                    "button_text": "Add Account"
                                }
                            ]
                        },
                        {
                            "buttons": [
                                {
                                    "id": "101",
                                    "type": "Simple",
                                    "button_text": "Edit Account"
                                },
                                {
                                    "id": "102",
                                    "type": "Simple",
                                    "button_text": "Remove Account"
                                }
                            ]
                        }
                    ]
                }
            }'

    import requests
    import json

    url = f"https://botapi.rubika.ir/v3/{token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": "Welcome",
        "inline_keypad": {
            "rows": [
                {
                    "buttons": [
                        {
                            "id": "100",
                            "type": "Simple",
                            "button_text": "Add Account"
                        }
                    ]
                },
                {
                    "buttons": [
                        {
                            "id": "101",
                            "type": "Simple",
                            "button_text": "Edit Account"
                        },
                        {
                            "id": "102",
                            "type": "Simple",
                            "button_text": "Remove Account"
                        }
                    ]
                }
            ]
        }
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=data)

    print(response.text)

    from rubika_bot.requests import send_message
    from rubika_bot.models import Keypad, KeypadRow, Button

    b1 = Button(id='100', type='Simple', button_text='Add Account')
    b2 = Button(id='101', type='Simple', button_text='Edit Account')
    b3 = Button(id='102', type='Simple', button_text='Remove Account')
    keypad = Keypad(
        rows=[
            KeypadRow(buttons=[b1]),
            KeypadRow(buttons=[b2, b3])
        ],
    )
    send_message(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        text='Welcome',
        inline_keypad=keypad
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/sendMessage',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          "chat_id": chat_id,
          "text": "hello world"
          "inline_keypad": {
            "rows": [
              {
                "buttons": [
                  {
                    "id": "100",
                    "type": "Simple",
                    "button_text": "Add Account"
                  }
                ]
              },
              {
                "buttons": [
                  {
                    "id": "101",
                    "type": "Simple",
                    "button_text": "Edit Account"
                  },
                  {
                    "id": "102",
                    "type": "Simple",
                    "button_text": "Remove Account"
                  }
                ]
              }
            ]
          }
        })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ارسال keypad¶

    متد: sendMessage
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
text 	string 	متن پیام
chat_keypad_type 	ChatKeypadTypeEnum 	نوع keypad
chat_keypad 	Keypad 	keypad
disable_notification 	bool 	مشخص می‌کند آیا اعلان‌ها غیرفعال شوند یا خیر (پیش‌فرض: false)
reply_to_message_id 	string 	شناسه پیام برای ریپلای

    خروجی

فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/sendMessage' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "text": "Welcome",
                "chat_keypad_type": "New",
                "chat_keypad": {
                    "rows": [
                        {
                            "buttons": [
                                {
                                    "id": "100",
                                    "type": "Simple",
                                    "button_text": "Add Account"
                                }
                            ]
                        },
                        {
                            "buttons": [
                                {
                                    "id": "101",
                                    "type": "Simple",
                                    "button_text": "Edit Account"
                                },
                                {
                                    "id": "102",
                                    "type": "Simple",
                                    "button_text": "Remove Account"
                                }
                            ]
                        }
                    ],
                    "resize_keyboard": true,
                    "one_time_keyboard": false
                }
            }'

    import requests
    import json

    url = f"https://botapi.rubika.ir/v3/{token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": "Welcome",
        "chat_keypad_type": "New",
        "chat_keypad": {
            "rows": [
                {
                    "buttons": [
                        {
                            "id": "100",
                            "type": "Simple",
                            "button_text": "Add Account"
                        }
                    ]
                },
                {
                    "buttons": [
                        {
                            "id": "101",
                            "type": "Simple",
                            "button_text": "Edit Account"
                        },
                        {
                            "id": "102",
                            "type": "Simple",
                            "button_text": "Remove Account"
                        }
                    ]
                }
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=data)

    print(response.text)

    from rubika_bot.requests import send_message
    from rubika_bot.models import Keypad, KeypadRow, Button

    b1 = Button(id='100', type='Simple', button_text='Add Account')
    b2 = Button(id='101', type='Simple', button_text='Edit Account')
    b3 = Button(id='102', type='Simple', button_text='Remove Account')
    keypad = Keypad(
        rows=[
            KeypadRow(buttons=[b1]),
            KeypadRow(buttons=[b2, b3])
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    send_message(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        text='Welcome',
        chat_keypad_type='New',
        chat_keypad=keypad
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/sendMessage',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          "chat_id": chat_id,
          "chat_keypad_type": "New",
          "text": "Welcome",
          "chat_keypad": {
            "rows": [
              {
                "buttons": [
                  {
                    "id": "100",
                    "type": "Simple",
                    "button_text": "Add Account"
                  }
                ]
              },
              {
                "buttons": [
                  {
                    "id": "101",
                    "type": "Simple",
                    "button_text": "Edit Account"
                  },
                  {
                    "id": "102",
                    "type": "Simple",
                    "button_text": "Remove Account"
                  }
                ]
              }
            ],
            "resize_keyboard": true,
            "one_time_keyboard": false
          }
        })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ارسال پیام متنی¶

    متد: sendMessage
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
text 	string 	متن پیام
disable_notification 	bool 	مشخص می‌کند آیا اعلان‌ها غیرفعال شوند یا خیر (پیش‌فرض: false)
reply_to_message_id 	string 	شناسه پیام برای ریپلای

    خروجی

فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/sendMessage' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "text": "Hello user, this is my text",
                "chat_id": "{chat_id}"
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "text": "Hello user, this is my text",
    }
    url = f'https://botapi.rubika.ir/v3/{token}/sendMessage'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import send_message

    send_message(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        text='Hello World',
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/sendMessage',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "text": "Hello user, this is my text"
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ارسال متادیتا ¶

    متد: sendMessage
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
text 	string 	متن پیام
metadata 	Metadata 	متادیتای مربوط به فرمت‌بندی، لینک، منشن و سایر ویژگی‌ها
disable_notification 	bool 	مشخص می‌کند آیا اعلان‌ها غیرفعال شوند یا خیر (پیش‌فرض: false)
reply_to_message_id 	string 	شناسه پیام برای ریپلای

    خروجی

فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/sendMessage' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "text": "سلام کاربر عزیز!",
                "metadata": {
                    "meta_data_parts": [
                        {
                                "type": "Bold",
                                "from_index": 0,
                                "length": 16
                        },
                        {
                                "type": "MentionText",
                                "from_index": 5,
                                "length": 11,
                                "mention_text_user_id": "user_id"
                        }
                    ]
                }
            }'

    import requests
    import json

    url = f"https://botapi.rubika.ir/v3/{token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": "سلام کاربر عزیز!",
        "metadata": {
           "meta_data_parts": [
               {
                       "type": "Bold",
                       "from_index": 0,
                       "length": 16
               },
               {
                       "type": "MentionText",
                       "from_index": 5,
                       "length": 11,
                       "mention_text_user_id": "user_id"
               }
           ]
       }
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=data)

    print(response.text)

    from rubika_bot.requests import send_message
    from rubika_bot.models import Keypad, KeypadRow, Button

    b1 = Button(id='100', type='Simple', button_text='Add Account')
    b2 = Button(id='101', type='Simple', button_text='Edit Account')
    b3 = Button(id='102', type='Simple', button_text='Remove Account')
    keypad = Keypad(
        rows=[
            KeypadRow(buttons=[b1]),
            KeypadRow(buttons=[b2, b3])
        ],
    )
    send_message(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        text='Welcome',
        inline_keypad=keypad
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/sendMessage',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          "chat_id": chat_id,
          "text": "سلام کاربر عزیز!"
          "metadata": {
            "meta_data_parts": [
              {
                 "type": "Bold",
                 "from_index": 0,
                 "length": 16
              },
              {
                 "type": "MentionText",
                 "from_index": 5,
                 "length": 11,
                 "mention_text_user_id": "user_id"
              }
            ]
          }
        })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ارسال نظرسنجی¶

    متد: sendPoll
    این متد امکان ارسال نظرسنجی از بات به چت را فراهم می‌کند، شامل سوال، گزینه‌ها و تنظیمات تعامل کاربران با نظرسنجی.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
question 	string 	متن سوال
options 	list[string] 	گزینه‌های سوال

    خروجی

فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/sendPoll' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "question": "Do you have any question?",
                "options": ["yes", "no"]
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "question": "Do you have any question?",
        "options": ["yes", "no"],
    }
    url = f'https://botapi.rubika.ir/v3/{token}/sendPoll'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import send_poll

    send_poll(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        question='Do you have any question?',
        options=['yes', 'no']
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/sendPoll',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "question": "Do you have any question?",
        "options": ["yes", "no"],
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ارسال موقعیت مکانی¶

    متد: sendLocation
    این متد موقعیت مکانی را از بات به چت ارسال می‌کند و شامل مختصات طول و عرض جغرافیایی است.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
latitude 	string 	عرض جغرافیایی
longitude 	string 	طول جغرافیایی
chat_keypad 	Keypad 	keypad
disable_notification 	string 	مشخص می‌کند آیا اعلان‌ها غیرفعال شوند یا خیر (پیش‌فرض: false)
inline_keypad 	Keypad 	Keypad
reply_to_message_id 	string 	شناسه پیام برای ریپلای
chat_keypad_type 	ChatKeypadTypeEnum 	نوع keypad

    خروجی

فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/sendLocation' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "latitude": "{latitude}",
                "longitude": "{longitude}"
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "latitude": latitude,
        "longitude": longitude,
    }
    url = f'https://botapi.rubika.ir/v3/{token}/sendLocation'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import send_location

    send_location(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        latitude='35.759662741892626',
        longitude='51.4036344416759'
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/sendLocation',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "latitude": latitude,
        "longitude": longitude,
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ارسال مخاطب¶

    متد: sendContact
    این متد امکان ارسال اطلاعات تماس (شماره تلفن و نام فرد) از بات به چت را فراهم می‌کند تا کاربران بتوانند به‌طور مستقیم با آن تماس برقرار کنند.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
first_name 	string 	نام مخاطب
last_name 	string 	نام‌خانوادگی مخاطب
phone_number 	string 	شماره مخاطب
chat_keypad 	Keypad 	keypad
disable_notification 	string 	مشخص می‌کند آیا اعلان‌ها غیرفعال شوند یا خیر (پیش‌فرض: false)
inline_keypad 	Keypad 	keypad
reply_to_message_id 	string 	شناسه پیام برای ریپلای
chat_keypad_type 	ChatKeypadTypeEnum 	نوع keypad

    خروجی

فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/sendContact' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "first_name": "{first_name}",
                "last_name": "{last_name}",
                "phone_number": "{phone_number}"
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number,
    }
    url = f'https://botapi.rubika.ir/v3/{token}/sendContact'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import send_contact

    send_contact(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        first_name='Ali',
        last_name='Rn',
        phone_number='09038754321'
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/sendContact',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

دریافت اطلاعات چت¶

    متد: getChat
    این متد اطلاعات کامل یک چت مشخص را بازمیگرداند، شامل شناسه، نام، نوع، تصویر و تنظیمات آن، تا بات بتواند ویژگی‌ها و وضعیت چت را مدیریت یا بررسی کند.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت

    خروجی

فیلد 	نوع 	توضیحات
chat 	Chat 	چت

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/getChat' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}"
            }'

    import requests

    data = {
        "chat_id": chat_id,
    }
    url = f'https://botapi.rubika.ir/v3/{token}/getChat'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import get_chat
    from rubika_bot.models import Chat

    chat: Chat = get_chat(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/getChat',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

دریافت آخرین آپدیت‌ها¶

    متد: getUpdates
    این متد تمامی پیام‌ها، ویرایش‌ها و رویدادهای جدید مربوط به چت‌ها را از سرور دریافت می‌کند. با استفاده از آن، بات می‌تواند فعالیت‌های کاربران، پاسخ‌ها، و تغییرات پیام‌ها را دنبال کند.
    ورودی

فیلد 	نوع 	توضیحات
offset_id 	string 	شناسه‌ای برای دریافت ادامه‌ی لیست. در صورت تمایل به دریافت پیام‌های بعدی، مقدار next_offset_id درخواست قبلی را در این فیلد قرار دهید.
limit 	int 	تعداد رکوردهای هر درخواست

    خروجی

فیلد 	نوع 	توضیحات
updates 	list[Update] 	آرایه‌ای از آپدیت ها
next_offset_id 	string 	شناسه‌ای برای درخواست بعدی جهت دریافت ادامه‌ی داده‌ها.

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/getUpdates' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "limit": "{limit}"
            }'

    import requests

    data = {
        "limit": limit,
    }
    url = f'https://botapi.rubika.ir/v3/{token}/getUpdates'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import get_updates
    from rubika_bot.models import Update

    updates, _ = get_updates(
        token='SUPER_SECRET_TOKEN',
        limit=10,
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/getUpdates',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "limit": limit,
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

فوروارد کردن پیام¶

    متد: forwardMessage
    این متد پیام موجود در یک چت را به چت دیگری منتقل می‌کند، بدون تغییر محتوا و با حفظ اطلاعات اصلی پیام.
    ورودی

فیلد 	نوع 	توضیحات
from_chat_id 	string 	از چتِ؟
message_id 	string 	شناسه پیام
to_chat_id 	string 	به چتِ؟
disable_notification 	bool 	مشخص می‌کند آیا اعلان‌ها غیرفعال شوند یا خیر (پیش‌فرض: false)

    خروجی

فیلد 	نوع 	توضیحات
new_message_id 	string 	شناسه پیام جدید

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/forwardMessage' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "from_chat_id": "{chat_id}",
                "message_id": "{message_id}",
                "to_chat_id": "{to_chat_id}"
            }'

    import requests

    data = {
        "from_chat_id": chat_id,
        "message_id": message_id,
        "to_chat_id": to_chat_id
    }
    url = f'https://botapi.rubika.ir/v3/{token}/forwardMessage'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import forward_message

    forward_message(
        token='SUPER_SECRET_TOKEN',
        from_chat_id='FIRST_CHAT_ID',
        message_id='MESSAGE_ID',
        to_chat_id='SECOND_CHAT_ID'
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/forwardMessage',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        "to_chat_id": to_chat_id
      })
    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ویرایش متن پیام¶

    متد: editMessageText
    این متد متن یک پیام ارسال‌شده توسط بات را ویرایش می‌کند، بدون ایجاد پیام جدید در چت.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
message_id 	string 	شناسه پیام
text 	string 	پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/editMessageText' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "message_id": "{message_id}",
                "text": "this is my new text"
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": "this is my new text"
    }
    url = f'https://botapi.rubika.ir/v3/{token}/editMessageText'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import edit_message_text

    edit_message_text(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        message_id='MESSAGE_ID',
        text='New Message Text'
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/editMessageText',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "message_id": message_id,
        "text": "this is my new text"
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ویرایش Inline Keypad¶

    متد: editMessageKeypad
    این متد صفحه‌کلید (InlineKeypad) یک پیام موجود را به‌روزرسانی می‌کند، بدون تغییر متن پیام.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
message_id 	string 	شناسه پیام
inline_keypad 	Keypad 	Keypad

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/editInlineKeypad' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "message_id": "{message_id}",
                "inline_keypad": {
                    "rows": [
                        {
                            "buttons": [
                                {
                                    "id": "100",
                                    "type": "Simple",
                                    "button_text": "Add Account"
                                }
                            ]
                        },
                        {
                            "buttons": [
                                {
                                    "id": "101",
                                    "type": "Simple",
                                    "button_text": "Edit Account"
                                },
                                {
                                    "id": "102",
                                    "type": "Simple",
                                    "button_text": "Remove Account"
                                }
                            ]
                        }
                    ]
                }
            }'

    import requests
    import json

    url = f"https://botapi.rubika.ir/v3/{token}/editMessageText"

    data = {
      "chat_id": chat_id,
      "message_id": message_id,
      "inline_keypad": {
        "rows": [
          {
            "buttons": [
              {
                "id": "100",
                "type": "Simple",
                "button_text": "Add Account"
              }
            ]
          },
          {
            "buttons": [
              {
                "id": "101",
                "type": "Simple",
                "button_text": "Edit Account"
              },
              {
                "id": "102",
                "type": "Simple",
                "button_text": "Remove Account"
              }
            ]
          }
        ]
      }
    }
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=data)

    print(response.text)

    from rubika_bot.requests import edit_message_keypad
    from rubika_bot.models import Button, Keypad, KeypadRow

    b1 = Button(id='100', type='Simple', button_text='Add Account')
    b2 = Button(id='101', type='Simple', button_text='Edit Account')
    b3 = Button(id='102', type='Simple', button_text='Remove Account')
    new_keypad = Keypad(
        rows=[
            KeypadRow(buttons=[b1]),
            KeypadRow(buttons=[b2, b3])
        ],
    )

    edit_message_keypad(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        message_id='MESSAGE_ID',
        inline_keypad=new_keypad
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/editMessageText',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          "chat_id": chat_id,
          "message_id": message_id,
          "inline_keypad": {
            "rows": [
              {
                "buttons": [
                  {
                    "id": "100",
                    "type": "Simple",
                    "button_text": "Add Account"
                  }
                ]
              },
              {
                "buttons": [
                  {
                    "id": "101",
                    "type": "Simple",
                    "button_text": "Edit Account"
                  },
                  {
                    "id": "102",
                    "type": "Simple",
                    "button_text": "Remove Account"
                  }
                ]
              }
            ]
          }
        })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

حذف پیام¶

    متد: deleteMessage
    این متد یک پیام مشخص را از چت حذف می‌کند، شامل پیام‌های ارسالی بات یا پیام‌های دیگران (در صورت داشتن مجوز).
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
message_id 	string 	شناسه پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/deleteMessage' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "message_id": "{message_id}"
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "message_id": chat_id
    }
    url = f'https://botapi.rubika.ir/v3/{token}/deleteMessage'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import delete_message

    delete_message(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        message_id='MESSAGE_ID',
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/deleteMessage',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "message_id": message_id
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

تنظیم دستور‌ها (commands)¶

    متد: setCommands
    این متد فهرست دستورات قابل استفاده بات را تعریف یا به‌روزرسانی می‌کند تا کاربر بتواند آنها را در رابط بات مشاهده کند.
    ورودی

فیلد 	نوع 	توضیحات
bot_commands 	list[BotCommand] 	آرایه‌ای از دستورات

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/setCommands' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "bot_commands": [
                    {
                        "command": "command1",
                        "description": "description1"
                    },
                    {
                        "command": "command2",
                        "description": "description2"
                    },
                ]
            }'

    import requests

    data = {
        "bot_commands": [
            {
                "command": "command1",
                "description": "description1"
            },
            {
                "command": "command2",
                "description": "description2"
            },
        ]
    }
    url = f'https://botapi.rubika.ir/v3/{token}/setCommands'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import set_commands
    from rubika_bot.models import BotCommand

    commands = [
        BotCommand(command='command1', description='description 1'),
        BotCommand(command='command2', description='description 2'),
    ]
    set_commands(token='SUPER_SECRET_TOKEN', bot_commands=commands)

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/setCommands',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          "bot_commands": [
              {
                  "command": "command1",
                  "description": "description1"
              },
              {
                  "command": "command2",
                  "description": "description2"
              },
          ]
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

آپدیت آدرس بات (URL Endpoint)¶

    متد: updateBotEndpoints
    این متد آدرس‌های endpoint بات را به‌روزرسانی می‌کند تا سرور بتواند رویدادها و درخواست‌ها را به آدرس‌های جدید ارسال کند.
    ورودی

فیلد 	نوع 	توضیحات
url 	string 	آدرس جدید
type 	UpdateEndpointTypeEnum 	نوع آدرس

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/updateBotEndpoints' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "url": "https://example.com",
                "type": "GetSelectionItem"
            }'

    import requests

    data = {
        'url': 'https://example.com',
        'type': 'GetSelectionItem',
    }
    url = f'https://botapi.rubika.ir/v3/{token}/updateBotEndpoints'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import update_bot_endpoint


    update_bot_endpoint(token='SUPER_SECRET_TOKEN', url='https://example.com', type='GetSelectionItem')

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/updateBotEndpoints',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "url": 'https://example.com',
        "type": "GetSelectionItem"
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

حذف keypad¶

    متد: editChatKeypad
    این متد با مشخص کردن پارامتر chat_keypad_type با مقدار Remove، صفحه‌کلید مرتبط با چت را حذف می‌کند و گزینه‌های تعاملی موجود در پیام‌ها را از بین می‌برد.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
chat_keypad_type 	ChatKeypadTypeEnum 	مقدارِ Remove

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/editChatKeypad' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "chat_keypad_type": "Remove"
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "chat_keypad_type": "Remove",
    }
    url = f'https://botapi.rubika.ir/v3/{token}/editChatKeypad'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import remove_chat_keypad

    remove_chat_keypad(token='SUPER_SECRET_TOKEN', chat_id='CHAT_ID')

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/editChatKeypad',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "chat_keypad_type": "Remove"
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ویرایش keypad¶

    متد: editChatKeypad
    برای ویرایش صفحه‌کلید مرتبط با چت، باید پارامتر chat_keypad_type را برابر New قرار دهید؛ این متد صفحه‌کلید مرتبط با چت را به‌روزرسانی می‌کند.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
chat_keypad 	Keypad 	keypad
chat_keypad_type 	ChatKeypadTypeEnum 	مقدارِ New

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/editChatKeypad' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "chat_keypad_type": "New",
                "chat_keypad": {
                    "rows": [
                        {
                            "buttons": [
                                {
                                    "id": "100",
                                    "type": "Simple",
                                    "button_text": "Add Account"
                                }
                            ]
                        },
                        {
                            "buttons": [
                                {
                                    "id": "101",
                                    "type": "Simple",
                                    "button_text": "Edit Account"
                                },
                                {
                                    "id": "102",
                                    "type": "Simple",
                                    "button_text": "Remove Account"
                                }
                            ]
                        }
                    ],
                    "resize_keyboard": true,
                    "one_time_keyboard": false
                }
            }'

    import requests

    url = f"https://botapi.rubika.ir/v3/{token}/editChatKeypad"

    data = {
        "chat_id": chat_id,
        "chat_keypad_type": "New",
        "chat_keypad": {
            "rows": [
                {
                    "buttons": [
                        {
                            "id": "100",
                            "type": "Simple",
                            "button_text": "Add Account"
                        }
                    ]
                },
                {
                    "buttons": [
                        {
                            "id": "101",
                            "type": "Simple",
                            "button_text": "Edit Account"
                        },
                        {
                            "id": "102",
                            "type": "Simple",
                            "button_text": "Remove Account"
                        }
                    ]
                }
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=data)

    print(response.text)

    from rubika_bot.requests import edit_chat_keypad
    from rubika_bot.models import Keypad, KeypadRow, Button

    b1 = Button(id='100', type='Simple', button_text='Add Account')
    b2 = Button(id='101', type='Simple', button_text='Edit Account')
    b3 = Button(id='102', type='Simple', button_text='Remove Account')
    keypad = Keypad(
        rows=[
            KeypadRow(buttons=[b1]),
            KeypadRow(buttons=[b2, b3])
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    edit_chat_keypad(token='SUPER_SECRET_TOKEN', chat_id='CHAT_ID', chat_keypad=keypad)

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/editChatKeypad',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          "chat_id": chat_id,
          "chat_keypad_type": "New",
          "chat_keypad": {
            "rows": [
              {
                "buttons": [
                  {
                    "id": "100",
                    "type": "Simple",
                    "button_text": "Add Account"
                  }
                ]
              },
              {
                "buttons": [
                  {
                    "id": "101",
                    "type": "Simple",
                    "button_text": "Edit Account"
                  },
                  {
                    "id": "102",
                    "type": "Simple",
                    "button_text": "Remove Account"
                  }
                ]
              }
            ],
            "resize_keyboard": true,
            "one_time_keyboard": false
          }
        })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

دریافت فایل¶

    متد: getFile
    این متد مسیر دانلود یک فایل آپلود شده را بازمیگرداند، تا بات بتواند فایل را دریافت کند.
    ورودی

فیلد 	نوع 	توضیحات
file_id 	string 	شناسه فایل

    خروجی

فیلد 	نوع 	توضیحات
download_url 	string 	آدرس فایل در سرور

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/getFile' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "file_id": "{file_id}"
            }'

    import requests

    data = {
        "file_id": file_id,
    }
    url = f'https://botapi.rubika.ir/v3/{token}/getFile'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import get_file
    from rubika_bot.models import File

    file: File = get_file(
        token='SUPER_SECRET_TOKEN',
        file_id='FILE_ID',
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/getFile',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "file_id": file_id
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

ارسال فایل¶

    متد: sendFile
    این متد فایل مشخص شده را از بات به چت ارسال می‌کند، فایل میتواند شامل محتوا و گزینه‌های اضافی مانند متن همراه یا صفحه‌کلید باشد.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
file_id 	string 	شناسه فایل
text 	string 	متن
reply_to_message_id 	string 	شناسه پیام برای ریپلای
disable_notification 	string 	مشخص می‌کند آیا اعلان‌ها غیرفعال شوند یا خیر (پیش‌فرض: false)
chat_keypad 	Keypad 	keypad
inline_keypad 	Keypad 	keypad
chat_keypad_type 	ChatKeypadTypeEnum 	نوع keypad

    خروجی

فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/sendFile' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "file_id": "{file_id}",
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "file_id": file_id,
    }
    url = f'https://botapi.rubika.ir/v3/{token}/sendFile'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import sendFile

    send_sticker(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        file_id='FILE_ID',
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/sendFile',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "file_id": file_id,
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

آپلود فایل¶

    متد: requestSendFile
    این متد به بات امکان می‌دهد نوع فایل مورد نظر برای آپلود را مشخص کند و در پاسخ، یک آدرس برای بارگذاری فایل دریافت می‌کند تا فایل مورد نظر از طریق آن آدرس به سرور ارسال شود.
    ورودی

فیلد 	نوع 	توضیحات
type 	FileTypeEnum 	نوع فایل

    خروجی

فیلد 	نوع 	توضیحات
upload_url 	string 	آدرس مخصوص آپلود فایل در سرور

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/requestSendFile' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "type": "Image",
            }'

    import requests

    data = {
        "type": "Image",
    }
    url = f'https://botapi.rubika.ir/v3/{token}/requestSendFile'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import requestSendFile

    send_sticker(
        token='SUPER_SECRET_TOKEN',
        type="Image",
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/requestSendFile',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "type": "Image",
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

آدرس دریافت شده در یک فیلد با نام upload_url برمی‌گردد که برای آپلود فایل از طریق درخواست POST استفاده می‌شود. فایل باید در بدنه (Body) درخواست ارسال گردد.

    ورودی

فیلد 	نوع 	توضیحات
file 	(multipart/form-data) 	فایل

    خروجی

فیلد 	نوع 	توضیحات
file_id 	string 	شناسه فایل
مسدود کردن کاربر¶

    متد: banChatMember
    این متد برای مسدود کردن یک کاربر در گروه یا کانال استفاده می‌شود. با اجرای این متد، کاربر از چت حذف می‌شود و تا زمان رفع مسدودی، امکان ورود مجدد او از طریق لینک دعوت وجود ندارد؛ با این حال، ادمین می‌تواند کاربر را به‌صورت دستی به چت اضافه کند. این متد روی مالک و ادمین‌ها اعمال نمی‌شود.
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
user_id 	string 	شناسه کاربر

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/banChatMember' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "user_id": "{user_id}",
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "user_id": user_id,
    }
    url = f'https://botapi.rubika.ir/v3/{token}/banChatMember'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import banChatMember

    send_sticker(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        user_id='َUSER_ID',
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/banChatMember',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "user_id": user_id,
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });

رفع مسدودیت کاربر ¶

    متد: unbanChatMember
    این متد برای رفع مسدودیت یک کاربر در گروه یا کانال استفاده می‌شود. با اجرای این متد، کاربر مجاز به ورود مجدد به چت می‌شود و می‌تواند از طریق لینک دعوت یا اضافه شدن دستی توسط ادمین به چت برگردد
    ورودی

فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
user_id 	string 	شناسه کاربر

    مثال

    cURLPythonNodeJs

    curl --location -g --request POST 'https://botapi.rubika.ir/v3/{token}/unbanChatMember' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "chat_id": "{chat_id}",
                "user_id": "{user_id}",
            }'

    import requests

    data = {
        "chat_id": chat_id,
        "user_id": user_id,
    }
    url = f'https://botapi.rubika.ir/v3/{token}/unbanChatMember'
    response = requests.post(url, json=data)

    print(response.text)

    from rubika_bot.requests import unbanChatMember

    send_sticker(
        token='SUPER_SECRET_TOKEN',
        chat_id='CHAT_ID',
        user_id='َUSER_ID',
    )

    var request = require('request');
    var options = {
      'method': 'POST',
      'url': 'https://botapi.rubika.ir/v3/{token}/unbanChatMember',
      'headers': {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "chat_id": chat_id,
        "user_id": user_id,
      })

    };
    request(options, function (error, response) {
      if (error) throw new Error(error);
      console.log(response.body);
    });




rubika.ir
مدل ها - بات روبیکا
53–68 minutes
مدل ها
Chat¶

مدل Chat نمایانگر اطلاعات پایه‌ای یک چت در روبیکا است. یک چت می‌تواند مکالمه‌ی خصوصی با کاربر، گفت‌وگوی گروهی یا کانال باشد. این مدل معمولاً در خروجی متدهایی مانند getChat و همچنین در برخی رویدادهای دریافتی از بات استفاده می‌شود.
فیلد 	نوع 	توضیحات
chat_id 	string 	شناسه چت
chat_type 	ChatTypeEnum 	نوع چت (کاربر، گروه، کانال و …).
user_id 	string 	شناسه کاربر مقابل بات در چت‌های خصوصی است. (فقط در چت‌های خصوصی).
first_name 	string 	نام کاربر. (فقط در چت‌های خصوصی).
last_name 	string 	نام خانوادگی کاربر
title 	string 	عنوان گروه یا کانال (در چت‌های گروهی و کانال‌ها).
username 	string 	نام کاربری چت یا کاربر (در صورت تنظیم شدن).

توجه: بسته به نوع چت، برخی فیلدها ممکن است مقدار null داشته باشند.
File¶

نشان‌دهنده‌ی اطلاعات یک فایل است که در پیام‌ها استفاده می‌شود.
فیلد 	نوع 	توضیحات
file_id 	string 	شناسه فایل
file_name 	string 	نام فایل
size 	string 	حجم فایل (بر حسب بایت)
ForwardedFrom¶

اطلاعات مربوط به پیام‌های فوروارد شده (Forwarded) را نمایش می‌دهد. این مدل در فیلد forwarded_from داخل مدل Message قرار می‌گیرد و نشان می‌دهد پیام از چه نوع منبعی، از کجا و توسط چه کسی فوروارد شده است
فیلد 	نوع 	توضیحات
type_from 	ForwardedFromEnum 	نوع منبع فوروارد (کاربر، کانال یا بات).
message_id 	string 	شناسه پیام اصلی که فوروارد شده.
from_chat_id 	string 	شناسه چت مبدا که پیام از آن فوروارد شده.
from_sender_id 	string 	شناسه کاربری ارسال‌کننده‌ی اصلی پیام.
MessageTextUpdate¶

مدل MessageTextUpdate تغییرات متنی پیام‌ها را نمایش می‌دهد که در نتیجه تعامل کاربر با Inline Keypad رخ داده است. این مدل فقط در داده‌های ارسالی به وب‌هوک بات هنگام فعال شدن receiveInlineMessage بازگردانده می‌شود و برای اطلاع بات از پیام‌هایی است که متن آن‌ها به دنبال این تعامل تغییر کرده است.
فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام که متن آن تغییر کرده است.
text 	string 	متن جدید پیام پس از به‌روزرسانی.

توجه: این مدل توسط کاربر مستقیماً فراخوانی نمی‌شود و تنها زمانی فعال می‌شود که کاربر روی Inline Keypad کلیک کند و سرور روبیکا یک درخواست POST حاوی شیء InlineMessage به وب‌هوک شما ارسال نماید.
Bot¶

عمومی یک بات روبیکا است که توسط متدهایی مانند getMe بازگردانده می‌شود.
فیلد 	نوع 	توضیحات
bot_id 	string 	شناسه یکتا بات
bot_title 	string 	عنوان نمایش‌داده‌شده در پروفایل بات
avatar 	File 	تصویر پروفایل بات
description 	string 	توضیحات بات
username 	string 	نام‌کاربری بات
start_message 	string 	پیامی که هنگام شروع مکالمه با بات به کاربر نشان داده می‌شود
share_url 	string 	لینک قابل اشتراک‌گذاری بات برای دعوت کاربران
BotCommand¶

مدل BotCommand برای تعریف دستورهای (Commands) قابل استفاده در بات به‌کار می‌رود. این دستورات همان مواردی هستند که کاربر می‌تواند با / در چت بات وارد کند و معمولاً در لیست دستورات پیشنهادی بات نمایش داده می‌شوند.
فیلد 	نوع 	توضیحات
command 	string 	نام دستور بدون / (مثلاً start)
description 	string 	توضیح کوتاه درباره عملکرد دستور
Sticker¶

مدل Sticker برای نمایش اطلاعات استیکر ارسال‌شده در یک پیام به‌کار می‌رود. استیکرها نوع خاصی از رسانه هستند که معمولاً همراه با اموجی نمایش داده می‌شوند و می‌توانند به‌عنوان بخشی از پیام به بات ارسال شوند.
فیلد 	نوع 	توضیحات
sticker_id 	string 	شناسه استیکر
file 	File 	اطلاعات فایل استیکر
emoji_character 	string 	اموجی مرتبط با استیکر
ContactMessage¶

مدل ContactMessage برای نمایش پیام‌های حاوی اطلاعات تماس استفاده می‌شود. زمانی که کاربر اطلاعات تماس را از طریق بات ارسال کند، این مدل نمایانگر آن اطلاعات در پیام است.
فیلد 	نوع 	توضیحات
phone_number 	string 	شماره تلفن ارسال‌شده توسط کاربر.
first_name 	string 	نام شخص صاحب شماره.
last_name 	string 	نام خانوادگی شخص (در صورت موجود).
PollStatus¶

نشان‌دهنده‌ی وضعیت فعلی یک نظرسنجی (Poll) است.
فیلد 	نوع 	توضیحات
state 	PollStatusEnum 	وضعیت فعلی نظرسنجی
selection_index 	int 	شماره گزینه انتخاب‌شده توسط کاربر؛ در صورت عدم انتخاب، مقدار -1 بازگردانده می‌شود.
percent_vote_options 	list[int] 	درصد رأی‌های هر گزینه در نظرسنجی.
total_vote 	int 	تعداد کل آراء نظرسنجی
show_total_votes 	bool 	آیا تعداد آرا باید به کاربر نمایش داده شود یا خیر.
Poll¶

مدل Poll برای نمایش اطلاعات یک نظرسنجی استفاده می‌شود، شامل سؤال نظرسنجی، گزینه‌ها و وضعیت فعلی رأی‌دهی.
فیلد 	نوع 	توضیحات
question 	string 	متن سؤال نظرسنجی.
options 	list[string] 	آرایه‌ای از گزینه‌های قابل رأی‌دهی
poll_status 	PollStatus 	وضعیت جاری نظرسنجی
Location¶

مدل Location نمایانگر مختصات جغرافیایی (GIS) است.
فیلد 	نوع 	توضیحات
longitude 	string 	طول جغرافیایی
latitude 	string 	عرض جغرافیایی
ButtonSelectionItem¶

هر گزینه از لیست انتخابی که نمایش داده می‌شود با این مدل تعریف می‌شود.
فیلد 	نوع 	توضیحات
text 	string 	متن دکمه
image_url 	string 	آدرس تصویر مرتبط با گزینه (در صورت وجود).
type 	ButtonSelectionTypeEnum 	نوع نمایش دکمه
ButtonSelection¶

تنظیمات کامل یک دکمه‌ی انتخاب را پیام مشخص می‌کند. این مدل برای دکمه‌هایی با type = Selection به‌کار می‌رود و شامل داده‌های لیست گزینه‌ها، نحوه‌ی نمایش، انتخاب چندگانه و شناسه‌ی انتخاب است.
فیلد 	نوع 	توضیحات
selection_id 	string 	شناسه مربوط به لیست
search_type 	ButtonSelectionSearchEnum 	نحوه‌ی جستجو
get_type 	ButtonSelectionGetEnum 	نحوه‌ی دریافت آیتم‌ها (مثلاً آفلاین/سینک با سرور).
items 	list[ButtonSelectionItem] 	آرایه‌ای از ButtonSelectionItem ها
is_multi_selection 	bool 	تعیین می‌کند که کاربر می‌تواند چند گزینه انتخاب کند یا تنها یک گزینه.
columns_count 	string 	تعداد ستون‌هایی که آیتم‌ها در آن نمایش داده می‌شوند.
title 	string 	عنوان
ButtonCalendar¶

تنظیمات دکمه‌ی انتخاب تاریخ را پیام تعریف می‌کند.
فیلد 	نوع 	توضیحات
default_value 	Optional[string] 	مقدار پیش‌فرض تقویم. تاریخی که در ابتدا به کاربر نمایش داده می‌شود.
type 	ButtonCalendarTypeEnum 	نوع تقویم (تقویم شمسی یا میلادی).
min_year 	string 	حداقل سال قابل انتخاب در تقویم.
max_year 	string 	بیشینه سال قابل انتخاب در تقویم.
title 	string 	عنوان دکمه
ButtonNumberPicker¶

این مدل تنظیمات دکمه‌ای را تعریف می‌کند که به کاربر امکان انتخاب یک عدد از یک بازه‌ی مشخص را می‌دهد.
فیلد 	نوع 	توضیحات
min_value 	string 	حداقل مقدار قابل انتخاب.
max_value 	string 	بیشینه مقدار قابل انتخاب.
default_value 	Optional[string] 	مقدار پیشفرض
title 	string 	عنوان دکمه
ButtonStringPicker¶

تنظیمات دکمه‌ای را مشخص می‌کند که به کاربر اجازه می‌دهد یک مقدار را از میان لیستی از رشته‌ها انتخاب کند.
فیلد 	نوع 	توضیحات
items 	list[string] 	آرایه‌ای از رشته‌ها — گزینه‌های قابل انتخاب.
default_value 	Optional[string] 	مقدار پیشفرض
title 	Optional[string] 	عنوان دکمه
ButtonTextbox¶

تنظیمات یک دکمه‌ی ورودی متن را پیام تعریف می‌کند
فیلد 	نوع 	توضیحات
type_line 	ButtonTextboxTypeLineEnum 	تعیین می‌کند ورودی متن به صورت تک‌خطی یا چندخطی باشد.
type_keypad 	ButtonTextboxTypeKeypadEnum 	نوع صفحه‌کلید نمایش داده‌شده برای ورودی متن (رشته‌ای یا عددی).
place_holder 	Optional[string] 	متن placeholder که در فیلد ورودی نمایش داده می‌شود.
title 	Optional[string] 	عنوان دکمه
default_value 	Optional[string] 	مقدار پیشفرض
ButtonLocation¶

تنظیمات یک دکمه‌ی ورودی مکان را پیام تعریف می‌کند، شامل موقعیت‌های پیش‌فرض و نوع نمایش نقشه.
فیلد 	نوع 	توضیحات
default_pointer_location 	Location 	مختصات نقطه‌ی پیش‌فرض در نقشه.
default_map_location 	Location 	مختصات مرکز نقشه در نمای اولیه.
type 	ButtonLocationTypeEnum 	نوع تعامل نقشه (انتخاب یا مشاهده).
title 	Optional[string] 	عنوان دکمه
AuxData¶

برای نگهداری داده‌های کمکی مرتبط با پیام‌ها استفاده می‌شود و معمولاً در رویدادهای کلیک روی دکمه‌ها (در Update یا وب‌هوک) بازگردانده می‌شود
فیلد 	نوع 	توضیحات
start_id 	string 	شناسه‌ی شروع تعامل کاربر با بات که در صورت ورود کاربر از طریق لینک دارای پارامتر st مقداردهی می‌شود. این مقدار همان مقداری است که در لینک بات ارسال شده و در رویدادهای دریافتی Webhook از قابل دسترسی است.
button_id 	string 	شناسه دکمه‌ای که کاربر روی آن کلیک کرده است(در صورت وجود).
Button¶

مدل Button نمایانگر یک دکمه تعاملی در رابط کاربری پیام یا صفحه‌کلید بات است. دکمه‌ها می‌توانند در Inline Keypad (دکمه‌های شیشه‌ای زیر پیام) یا Chat Keypad (دکمه‌های کلید پایین پیام) نمایش داده شوند و برای ایجاد تعامل‌های مختلف (عملیات، انتخاب، ورودی کاربر، ارسال موقعیت و…) استفاده می‌شوند.
فیلد 	نوع 	توضیحات
id 	string 	شناسه دکمه
type 	ButtonTypeEnum 	نوع دکمه که مشخص می‌کند رفتار و شکل نمایش آن چگونه است.
button_text 	string 	متن نمایش‌داده‌شده روی دکمه.
button_selection 	ButtonSelection 	داده‌های مربوط به دکمه لیست انتخابی.
button_calendar 	ButtonCalendar 	داده‌های مربوط به دکمه تقویم.
button_number_picker 	ButtonNumberPicker 	داده‌های مربوط به دکمه انتخاب عدد.
button_string_picker 	ButtonStringPicker 	داده‌های مربوط به دکمه انتخاب رشته.
button_location 	ButtonLocation 	داده‌های مربوط به دکمه موقعیت.
button_textbox 	ButtonTextbox 	داده‌های مربوط به دکمه متن ورودی.

توجه: فیلدهای button_selection، button_calendar، button_number_picker، button_string_picker، button_location و button_textbox تنها زمانی پر می‌شوند که نوع دکمه (type) با همان مدل سازگار باشد.
ButtonTypeEnum¶

این Enum انواع مختلف رفتار و هدف دکمه را مشخص می‌کند.
فیلد 	نوع 	توضیحات
Simple 	string 	دکمه معمولی با متن ثابت.
Selection 	string 	دکمه‌ای برای نمایش لیست انتخابی.
Calendar 	string 	نمایش دکمه به صورت تقویم
NumberPicker 	string 	دکمه‌ای برای انتخاب عدد از محدودهٔ مشخص.
StringPicker 	string 	دکمه‌ای برای انتخاب مقدار از لیست رشته‌ها.
Location 	string 	دکمه‌ای برای اشتراک‌گذاری موقعیت مکانی.
CameraImage 	string 	دکمه‌ای برای گرفتن عکس با دوربین.
CameraVideo 	string 	دکمه‌ای برای گرفتن ویدئو با دوربین.
GalleryImage 	string 	دکمه‌ای برای انتخاب عکس از گالری.
GalleryVideo 	string 	دکمه‌ای برای انتخاب ویدئو از گالری.
File 	string 	دکمه‌ای برای انتخاب فایل.
Audio 	string 	دکمه‌ای برای انتخاب فایل صوتی.
RecordAudio 	string 	دکمه‌ای برای ضبط صدا.
Textbox 	string 	دکمه‌ای برای باز کردن ورودی متن.
Link 	string 	دکمه‌ای برای باز کردن لینک.
AskMyPhoneNumber 	string 	دکمه‌ای برای درخواست شماره تلفن کاربر.
AskMyLocation 	string 	دکمه‌ای برای درخواست موقعیت کاربر.
Barcode 	string 	دکمه‌ای برای اسکن بارکد.
KeypadRow¶

نمایانگر یک ردیف از دکمه‌ها در یک Keypad است. این مدل شامل آرایه‌ای از دکمه‌ها است که به‌صورت افقی در یک ردیف نمایش داده می‌شوند.
فیلد 	نوع 	توضیحات
buttons 	list[Button] 	آرایه‌ای از دکمه‌ها

توجه: ترتیب قرارگیری دکمه‌ها در آرایه، ترتیب نمایش افقی کلیدها را تعیین می‌کند.
Keypad¶

مدل Keypad مجموعه‌ای از ردیف‌های دکمه را تعریف می‌کند که می‌تواند در Keypad پیام (Inline یا Chat) نمایش داده شود.
فیلد 	نوع 	توضیحات
rows 	list[KeypadRow] 	آرایه‌ای از ردیف keypad ها
resize_keyboard 	bool 	تغییر اندازه و ارتفاع دکمه‌ها
one_time_keyboard 	bool 	بسته شدن خودکار کیبورد بعد از اولین انتخاب
MessageKeypadUpdate¶

مدل MessageKeypadUpdate برای به‌روزرسانی Inline Keypad پیام‌ها در پاسخ به رویداد کلیک کاربر روی Inline Keypad استفاده می‌شود. این مدل تنها در خروجی وب‌هوک receiveInlineMessage و به‌عنوان بخشی از پاسخ بات به پلتفرم بازگردانده می‌شود.
فیلد 	نوع 	توضیحات
message_id 	string 	شناسه‌ی پیام که Keypad آن تغییر یافته است.
inline_keypad 	Keypad 	Keypad جدید که باید جایگزین Keypad قبلی شود.
Message¶

مدل Message نمایانگر اطلاعات یک پیام در روبیکا است که می‌تواند شامل متن، فایل، موقعیت جغرافیایی، نظرسنجی.... و دیگر داده‌های مرتبط باشد. این مدل معمولاً در خروجی متدهای دریافت پیام (مانند getUpdates یا داده‌های وب‌هوک) و همچنین در پاسخ‌های بات استفاده می‌شود.
فیلد 	نوع 	توضیحات
message_id 	string 	شناسه پیام
text 	string 	متن پیام — اگر پیام متنی باشد.
time 	int 	زمان ارسال پیام به صورت timestamp.
is_edited 	bool 	نشان می‌دهد آیا پیام ویرایش شده است یا خیر.
sender_type 	MessageSenderEnum 	نوع فرستنده پیام
sender_id 	string 	شناسه فرستنده پیام
aux_data 	AuxData 	داده‌های کمکی مرتبط با پیام
file 	File 	اطلاعات فایل پیوست (اگر پیام شامل فایل باشد)
reply_to_message_id 	string 	شناسه پیام قبلی که این پیام در پاسخ به آن ارسال شده است.
forwarded_from 	ForwardedFrom 	اطلاعات اصلی پیام فوروارد شده (در صورت وجود).
forwarded_no_link 	string 	متنی که به‌جای لینک حساب کاربری فرستنده نمایش داده می‌شود، در صورتی که فرستنده اجازه لینک شدن به حساب خود را غیرفعال کرده باشد.
location 	Location 	موقعیت جغرافیایی ارسال‌شده (اگر پیام موقعیت داشته باشد).
sticker 	Sticker 	اطلاعات استیکر (در صورت وجود).
contact_message 	ContactMessage 	اطلاعات تماس اگر پیام حاوی Contact باشد.
poll 	Poll 	اطلاعات نظرسنجی اگر پیام شامل Poll باشد.
Update¶

نمایانگر رویدادی است که از سوی API یا وب‌هوک به بات می‌رسد و شامل داده‌های مرتبط با پیام‌ها و تغییرات آن‌ها می‌باشد.
فیلد 	نوع 	توضیحات
type 	UpdateTypeEnum 	نوع رویداد آپدیت (مثل پیام جدید، پیام ویرایش‌شده، حذف پیام و …).
chat_id 	string 	شناسه چت مرتبط با رویداد.
removed_message_id 	Optional[string] 	شناسه‌ی پیام حذف‌شده (در رویداد حذف پیام).
new_message 	Message 	پیام جدید در این رویداد (اگر نوع رویداد پیام جدید باشد).
updated_message 	Optional[Message] 	پیام ویرایش‌شده (در رویداد ویرایش پیام).
InlineMessage¶

داده‌های مربوط به کلیک کاربر روی Inline Keypad را در وب‌هوک receiveInlineMessage نمایش می‌دهد و شامل شناسه پیام و چت، داده‌های کمکی، متن و اطلاعات رسانه‌ای است.
فیلد 	نوع 	توضیحات
sender_id 	string 	شناسه کاربری که روی Inline Keypad کلیک کرده است.
text 	string 	متن پیام مرتبط (اگر وجود داشته باشد).
file 	Optional[File] 	فایل همراه پیام (اگر وجود داشته باشد).
location 	Optional[Location] 	موقعیت جغرافیایی (در صورت وجود).
aux_data 	Optional[AuxData] 	داده‌های کمکی مرتبط با کلیک دکمه.
message_id 	string 	شناسه پیام اصلی که InlineKeypad آن را نشان می‌دهد.
chat_id 	string 	شناسه چت مرتبط با پیام Inline.
Metadata¶

این مدل شامل لیستی از متادیتاها است که برای اعمال تغییرات مختلف روی متن پیام استفاده می‌شود.
فیلد 	نوع 	توضیحات
meta_data_parts 	list[MetadataPart] 	لیستی از متادیتاهایی که روی متن اعمال می شود. که حداکثر تعداد آن 30 می باشد

توجه : در صورت نامعتبر بودن حتی یک metadata، کل درخواست با خطا مواجه می‌شود و پیام ارسال نخواهد شد
MetadataPart¶

این مدل یک قطعه از متادیتا را تعریف می‌کند که نوع تغییر، موقعیت شروع و طول آن را در متن مشخص می‌کند. برخی انواع متادیتا ممکن است شامل فیلدهای اضافی باشند.
فیلد 	نوع 	توضیحات
type 	MetadataTypeEnum 	نوع متادیتا
from_index 	int 	اندیس شروع در متن (بر اساس UTF-16) که مقدار آن میتواند بزرگتر یا برابر 0 باشد.
length 	int 	طول بخش مورد نظر (بر اساس UTF-16) که باید حتما بزرگتر از 0 باشد.
link_url 	string 	فقط در صورتی که type برابر با Link باشد استفاده می‌شود.
mention_text_user_id 	string 	فقط در صورتی که type برابر با MentionText باشد استفاده می‌شود.

توجه: مجموع from_index + length نباید از طول متن (بر اساس UTF-16) بیشتر شود. در غیر این صورت مقادیر نامعتبر بوده و درخواست با خطا مواجه می‌شود و پیام ارسال نخواهد شد.

توجه: برخی کاراکترها (مانند emoji) دارای طول 2 هستند.

توجه: در نوع MentionText پیام باید در چت گروهی ارسال شود در غیر این صورت درخواست با خطا مواجه خواهد شد.

توجه: اعمال فرمت‌های Bold، Italic، Underline و Strike روی emoji تأثیر قابل مشاهده‌ای ندارد.
Enums¶
ChatTypeEnum¶
فیلد 	توضیحات
User 	چت با کاربر
Bot 	چت با ربات
Group 	چت در گروه
Channel 	چت در کانال
FileTypeEnum¶
فیلد 	توضیحات
File 	فایل‌های عمومی با حداکثر حجم 50 مگابایت.
Image 	عکس با فرمت jpg، gif، png یا webp با حداکثر حجم 10 مگابایت.
Voice 	پیام صوتی کوتاه با فرمت mp3.
Video 	فیلم با فرمت mp4 با حداکثر حجم 50 مگابایت.
Music 	آهنگ با فرمت mp3.
Gif 	تصویر متحرک با فرمت mp4 که حتماً باید بدون صدا باشد.
فیلد 	توضیحات
User 	پیام از یک کاربر فوروارد شده است.
Channel 	پیام از یک کانال فوروارد شده است.
Bot 	پیام از یک بات فوروارد شده است.
فیلد 	توضیحات
Paid 	پرداخت شده
NotPaid 	پرداخت نشده
PollStatusEnum¶
فیلد 	توضیحات
Open 	نظرسنجی در حال اجرا و قابل رأی دادن است.
Closed 	نظرسنجی پایان یافته و رأی‌دهی بسته است.
ButtonSelectionTypeEnum¶
فیلد 	توضیحات
TextOnly 	نمایش دکمه به صورت متن
TextImgThu 	نمایش دکمه به صورت متن و عکس کوچک
TextImgBig 	نمایش دکمه به صورت متن و عکس بزرگ
ButtonSelectionSearchEnum¶
فیلد 	توضیحات
None 	حالت پیشفرض
Local 	جستجو در آیتم‌های لیست با استفاده از مقادیر ارسالی در فیلد items
Api 	جستجو در آیتم‌های لیست از طریق Api
ButtonSelectionGetEnum¶
فیلد 	توضیحات
Local 	نمایش آیتم‌های لیست با استفاده از مقادیر ارسالی در فیلد items
Api 	جستجو در آیتم‌های لیست از طریق Api
ButtonCalendarTypeEnum¶
فیلد 	توضیحات
DatePersian 	نمایش تقویم به فرمت شمسی
DateGregorian 	نمایش تقویم به فرمت میلادی
ButtonTextboxTypeKeypadEnum¶
فیلد 	نوع 	توضیحات
String 	string 	امکان ارسال تمامی کاراکتر ها
Number 	string 	امکان ارسال کاراکترها عددی
ButtonTextboxTypeLineEnum¶
فیلد 	نوع 	توضیحات
SingleLine 	string 	نوشتن پیام متنی در یک سطر
MultiLine 	string 	نوشتن پیام متنی در چندین سطر
ButtonLocationTypeEnum¶
فیلد 	توضیحات
Picker 	به کاربر اجازه می‌دهد موقعیت را انتخاب کند (Picker).
View 	موقعیت به صورت نمایشی نشان داده می‌شود (View).
MessageSenderEnum¶
فیلد 	توضیحات
User 	کاربر
Bot 	بات
UpdateTypeEnum¶
فیلد 	توضیحات
UpdatedMessage 	ویرایش پیام
NewMessage 	پیام جدید
RemovedMessage 	حذف پیام
StartedBot 	شروع بات
StoppedBot 	توقف بات
ChatKeypadTypeEnum¶
فیلد 	توضیحات
None 	مقدار پیشفرض
New 	اضافه کردن keypad جدید
Remove 	حذف keypad
UpdateEndpointTypeEnum¶
فیلد 	توضیحات
ReceiveUpdate 	ReceiveUpdate
ReceiveInlineMessage 	ReceiveInlineMessage
ReceiveQuery 	ReceiveQuery
GetSelectionItem 	GetSelectionItem
SearchSelectionItems 	SearchSelectionItems
MetadataTypeEnum¶
فیلد 	توضیحات
Bold 	متن برجسته
Italic 	متن کج
Mono 	متن تک‌فاصله
Underline 	زیرخط‌دار
Strike 	خط‌خورده
Spoiler 	اسپویل
Link 	لینک
MentionText 	منشن کاربر
Pre 	بلاک کد
Quote 	نقل قول



rubika.ir
گروه ها و کانال ها
8–10 minutes
گروه ها و کانال ها

بات‌ها در محیط‌های گروه و کانال رفتار و نقش متفاوتی نسبت به چت خصوصی دارند. در این جا توضیح داده می‌شود که چگونه توسعه‌دهنده می‌تواند رفتار بات را متناسب با سطح دسترسی، نوع تعامل و ساختار هر فضا تنظیم کند.
افزودن بات و ارتقاء بات به ادمین ¶

    برای استفاده کامل از بات، ابتدا باید آن را به در گروه یا کانال اضافه کنید و به ادمین ارتقاء دهید. مراحل به صورت زیر است.
    در نظر داشته باشید کاربر باید خودش دارای دسترسی ادمین باشد تا بتواند بات را اضافه و مدیریت کند.
    مراحل افزودن به گروه یا کانال
        به بخش افزودن عضو بروید.
        در نوار جستجو بالای صفحه، آی‌دی یا نام بات را وارد کنید.
        بات را از لیست نتایج انتخاب کنید و به گروه یا کانال اضافه کنید.
        بعد از اضافه شدن، وارد لیست اعضا شوید. بات را پیدا کنید و گزینه ارتقاء به ادمین را انتخاب کنید.
        پس از ارتقاء بات به ادمین، می‌توانید دسترسی‌های لازم برای بات را فعال یا غیرفعال کنید.
        پس از تنظیم دسترسی‌ها، تغییرات را ذخیره کنید.
    بات اکنون آماده استفاده در گروه یا کانال است و می‌تواند طبق دسترسی‌های داده شده عمل کند.

مدیریت عملکرد بات ¶

بعد از ادمین شدن، بات می‌تواند مجموعه‌ای از عملیات مدیریتی را در گروه یا کانال انجام دهد. این قابلیت‌ها شامل ارسال، حذف یا ویرایش پیام‌ها، پاسخ به پیام‌های کاربران، و حتی دیدن پیام ها توسط بات (در صورت داشتن مجوز) است.

در جدول زیر، مهم‌ترین عملکردهای بات و کاربرد هر یک آورده شده است.
متد 	توضیحات
sendMessage 	برای ارسال پیام متنی توسط بات در گروه، کانال یا چت خصوصی استفاده می‌شود. این متد از پارامترهایی مانند chat_id ،text و در صورت نیاز reply_to_message_id پشتیبانی می‌کند.
editMessageText 	متن پیامی که قبلاً ارسال شده را ویرایش می‌کند. این متد معمولاً برای به‌روزرسانی پیام‌های اطلاع‌رسانی یا اصلاح خطاها استفاده می‌شود.
deleteMessage 	پیامی را که بات یا کاربر ارسال کرده، حذف می‌کند.
sendFile 	برای ارسال فایل‌هایی مانند تصویر، ویدیو، سند یا فایل صوتی و ... به‌کار می‌رود. نوع فایل از طریق پارامتر type در هنگام صدا کردن متد requestSendFile مشخص می‌شود.
sendPoll 	جهت ایجاد نظرسنجی در چت‌ها به‌کار می‌رود. پارامترهای کلیدی آن شامل question و options هستند.
banChatMember 	این متد برای مسدود کردن یک کاربر در گروه یا کانال استفاده می‌شود.
unbanChatMember 	این متد برای رفع مسدودیت یک کاربر در گروه یا کانال استفاده می‌شود.
محدودیت ها و نکات امنیتی ¶

در این بخش به محدودیت‌های فنی و ملاحظات امنیتی مرتبط با عملکرد بات در گروه‌ها و کانال‌ها اشاره می‌شود.
محدودیت‌ها

    دسترسی محدود بات‌ به پیام‌ها:

    بات فقط پیام‌هایی را می‌بیند که به آن مربوط هستند. مثلاً پیام‌های که بات در آنها منشن شده و یا با کاراکتر "/" شروع میشوند.

    برای دسترسی کامل به همه پیام‌ها، باید گزینه "دریافت همه پیام های کانال و گروه" را از بخش تنظیمات در @BotFather روبیکا فعال کنید.
    محدودیت در ویرایش:

    در گروه‌ها، قابلیت editMessageText فقط برای پیام‌هایی فعال است که بات آن‌ها را ارسال کرده باشد.
    عدم امکان افزودن بات با لینک دعوت:

    افزودن بات به گروه یا کانال فقط از طریق ادمین و به‌صورت دستی انجام می‌شود.
    محدودیت تعداد بات‌های ادمین:

    توجه داشته باشید که در هر گروه یا کانال، به‌صورت هم‌زمان حداکثر ۱۰ بات می‌توانند به عنوان ادمین اضافه شوند.
    دسترسی بات به تغییرات پیام‌ها:

    بات‌ها تنها رویدادهای مربوط به ویرایش یا حذف پیام‌هایی را دریافت می‌کنند که توسط کاربران انسانی انجام شده باشد. تغییراتی که توسط خود بات یا سایر بات‌ها اعمال شود، قابل شناسایی نیست و رویدادی برای آن ارسال نمی‌شود.

نکات امنیتی

برای حفظ پایداری و جلوگیری از رفتارهای ناخواسته، تنظیمات امنیتی بات باید با دقت انجام شود. هنگام تعیین سطح دسترسی، تنها مجوزهایی را فعال کنید که واقعاً مورد نیاز هستند؛ اعطای دسترسی‌های بیش از حد (مانند حذف) می‌تواند باعث بروز خطا یا حذف ناخواسته‌ی داده‌ها شود.

همچنین توصیه می‌شود بات فقط به پیام‌های خاص (مثلاً شامل دستورات یا کلیدواژه‌های مشخص) پاسخ دهد تا از تولید هرزپیام یا ایجاد اختلال در جریان گفتگو جلوگیری شود.

در نهایت، برای پایش رفتار بات و خطاهای احتمالی، توصیه می‌شود لاگ رویدادها (به‌ویژه خطاها و دستورات اجراشده) ذخیره شود.
