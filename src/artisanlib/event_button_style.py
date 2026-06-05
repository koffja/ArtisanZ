from artisanlib.util import createGradient

artisan_event_button_style: str = """
            EventPushButton {{
                min-width: {min_width}px;
                min-height: {min_height}px;
                font-size: {default_font_size}pt;
                font-weight: bold;
                padding: {padding}px;
                border-style:solid;
                border-radius:4;
                border-color:grey;
                border-width:0;
                color: white;
            }}

            EventPushButton[Selected=true] {{
                font-size: {selected_font_size}pt;
                background-color:""" + createGradient('#A76557') + """ ;
            }}
            EventPushButton[Selected=true]:flat {{
                color: darkgrey;
                background-color: #F2E0D8;
            }}
            EventPushButton[Selected=true]:flat:!pressed:hover {{
                color: #F5F5F5;
                background-color: #D4B8A8;
            }}
            EventPushButton[Selected=true]:flat:pressed {{
                color: #EEEEEE;
                background-color: #A76557;
            }}
            EventPushButton[Selected=true]:!flat:pressed {{
                color: white;
                background-color:""" + createGradient('#865146') + """ ;
            }}
            EventPushButton[Selected=true]:!pressed:hover {{
                color: white;
                background-color:""" + createGradient('#A76557') + """ ;
            }}

            MajorEventPushButton[Selected=false]:flat {{
                color: darkgrey;
                background-color: #E0E0E0;
            }}
            MajorEventPushButton[Selected=false]:flat:!pressed:hover {{
                color: #F5F5F5;
                background-color: #CDCDCD;
            }}
            MajorEventPushButton[Selected=false]:flat:pressed {{
                color: #EEEEEE;
                background-color: #9E9E9E;
            }}
            MajorEventPushButton[Selected=false]:!flat:pressed {{
                color: #EEEEEE;
                background-color:""" + createGradient('#3E5A66') + """ ;
            }}
            MajorEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#5E889A') + """ ;
            }}

            MinorEventPushButton[Selected=false]:flat {{
                color: #BDBDBD;
                background-color: #EEEEEE;
            }}
            MinorEventPushButton[Selected=false]:flat:!pressed:hover {{
                color: #F5F5F5;
                background-color: #DDDDDD;
            }}
            MinorEventPushButton[Selected=false]:flat:pressed {{
                color: #EEEEEE;
                background-color: #BEBEBE;
            }}
            MinorEventPushButton[Selected=false]:!flat:pressed {{
                color: #EEEEEE;
                background-color:""" + createGradient('#738185') + """ ;
            }}
            MinorEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#A6B5BB') + """ ;
            }}

            AuxEventPushButton[Selected=false]:pressed {{
                background-color:""" + createGradient('#9A6E55') + """ ;
            }}
            AuxEventPushButton[Selected=false]:!pressed:hover {{
                background-color:""" + createGradient('#D1A082') + """ ;
            }}
"""
