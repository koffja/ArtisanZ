artisan_event_button_style: str = """
            EventPushButton {{
                min-width: {min_width}px;
                min-height: {min_height}px;
                font-size: {default_font_size}pt;
                font-weight: bold;
                padding: {padding}px {padding}px;
                border: 1px solid #CDD7D8;
                border-radius: 8px;
                color: white;
            }}

            EventPushButton[Selected=true] {{
                font-size: {selected_font_size}pt;
                background-color: #B4685C;
            }}
            EventPushButton[Selected=true]:flat {{
                color: #8A4D43;
                background-color: #F0D7CE;
            }}
            EventPushButton[Selected=true]:flat:!pressed:hover {{
                color: #6F372F;
                background-color: #E8C8BE;
            }}
            EventPushButton[Selected=true]:flat:pressed {{
                color: #EEEEEE;
                background-color: #B4685C;
            }}
            EventPushButton[Selected=true]:!flat:pressed {{
                color: white;
                background-color: #8E4C43;
            }}
            EventPushButton[Selected=true]:!pressed:hover {{
                color: white;
                background-color: #C47A6F;
            }}

            MajorEventPushButton[Selected=false]:flat {{
                color: #376B7A;
                background-color: #E3ECEE;
            }}
            MajorEventPushButton[Selected=false]:flat:!pressed:hover {{
                color: #244E59;
                background-color: #D5E2E5;
            }}
            MajorEventPushButton[Selected=false]:flat:pressed {{
                color: #FFFFFF;
                background-color: #6E848B;
            }}
            MajorEventPushButton[Selected=false]:!flat:pressed {{
                color: #EEEEEE;
                background-color: #244E59;
            }}
            MajorEventPushButton[Selected=false]:!pressed:hover {{
                background-color: #467D8C;
            }}

            MinorEventPushButton[Selected=false]:flat {{
                color: #6F875E;
                background-color: #EEF3EA;
            }}
            MinorEventPushButton[Selected=false]:flat:!pressed:hover {{
                color: #546C44;
                background-color: #E1EAD9;
            }}
            MinorEventPushButton[Selected=false]:flat:pressed {{
                color: #FFFFFF;
                background-color: #7B8D6F;
            }}
            MinorEventPushButton[Selected=false]:!flat:pressed {{
                color: #EEEEEE;
                background-color: #5D704F;
            }}
            MinorEventPushButton[Selected=false]:!pressed:hover {{
                background-color: #839872;
            }}

            AuxEventPushButton[Selected=false]:pressed {{
                background-color: #8E4C43;
            }}
            AuxEventPushButton[Selected=false]:!pressed:hover {{
                background-color: #C47A6F;
            }}
"""
