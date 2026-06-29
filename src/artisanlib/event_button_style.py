artisan_event_button_style: str = """
            EventPushButton {{
                min-width: {min_width}px;
                min-height: {min_height}px;
                font-size: {default_font_size}pt;
                font-weight: bold;
                padding: {padding}px;
                border: 1px solid #cfd7db;
                border-radius: 6px;
                color: white;
            }}

            EventPushButton[Selected=true] {{
                font-size: {selected_font_size}pt;
                background-color: #A76557;
            }}
            EventPushButton[Selected=true]:flat {{
                color: #8A6B60;
                background-color: #F2E0D8;
            }}
            EventPushButton[Selected=true]:flat:!pressed:hover {{
                color: #5F4038;
                background-color: #EAD0C5;
            }}
            EventPushButton[Selected=true]:flat:pressed {{
                color: #EEEEEE;
                background-color: #A76557;
            }}
            EventPushButton[Selected=true]:!flat:pressed {{
                color: white;
                background-color: #865146;
            }}
            EventPushButton[Selected=true]:!pressed:hover {{
                color: white;
                background-color: #B87362;
            }}

            MajorEventPushButton[Selected=false]:flat {{
                color: #7B868C;
                background-color: #E8ECEE;
            }}
            MajorEventPushButton[Selected=false]:flat:!pressed:hover {{
                color: #4E7180;
                background-color: #DDE5E8;
            }}
            MajorEventPushButton[Selected=false]:flat:pressed {{
                color: #FFFFFF;
                background-color: #9DAAB0;
            }}
            MajorEventPushButton[Selected=false]:!flat:pressed {{
                color: #EEEEEE;
                background-color: #3E5A66;
            }}
            MajorEventPushButton[Selected=false]:!pressed:hover {{
                background-color: #5E889A;
            }}

            MinorEventPushButton[Selected=false]:flat {{
                color: #87939A;
                background-color: #EEF2F3;
            }}
            MinorEventPushButton[Selected=false]:flat:!pressed:hover {{
                color: #5D6970;
                background-color: #E1E8EA;
            }}
            MinorEventPushButton[Selected=false]:flat:pressed {{
                color: #FFFFFF;
                background-color: #9DAAB0;
            }}
            MinorEventPushButton[Selected=false]:!flat:pressed {{
                color: #EEEEEE;
                background-color: #738185;
            }}
            MinorEventPushButton[Selected=false]:!pressed:hover {{
                background-color: #A6B5BB;
            }}

            AuxEventPushButton[Selected=false]:pressed {{
                background-color: #9A6E55;
            }}
            AuxEventPushButton[Selected=false]:!pressed:hover {{
                background-color: #D1A082;
            }}
"""
