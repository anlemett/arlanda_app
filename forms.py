#from flask_wtf import Form
from wtforms import Form, validators
from wtforms import IntegerField, StringField, SelectField, FileField
#from wtforms import BooleanField, PasswordField, TextAreaField
from wtforms.fields.html5 import DateField,  TimeField
#from wtforms.validators import (DataRequired, Regexp, ValidationError, Length, EqualTo)

from datetime import datetime, date, time, timedelta


class TrajectoriesForm(Form):
    #date = DateField('Date:', [validators.InputRequired()], render_kw={"value": "2018-12-24"})
    #time_begin = TimeField('Start time:', [validators.InputRequired()], render_kw={"value": "00:00"})
    #time_end = TimeField('End time:', [validators.InputRequired()], render_kw={"value": "01:00"})
    date_begin = DateField('Start date:', [validators.InputRequired()], render_kw={"value": "2018-01-01"})
    date_end = DateField('End date:', [validators.InputRequired()], render_kw={"value": "2018-01-31"})
    callsign = StringField('Callsign:', [validators.DataRequired()])
    #in_out = SelectField('International/Domestic:', choices = [('all', 'All'),
    #    ('international', 'International'), ('domestic', 'Domestic')])


    def validate(self):
        if not super().validate():
            return False
        result = True
        #if (datetime.combine(self.date.data, self.time_begin.data).timestamp() > datetime.combine(self.date.data, self.time_end.data).timestamp()):
        #        self.time_end.errors.append('End time must be bigger than start time')
        #        result = False

        timestamp_begin = datetime.combine(self.date_begin.data, time.min).timestamp()
        timestamp_end = datetime.combine(self.date_end.data, time.max).timestamp()
        
        first_timestamp = int(datetime(2018, 1, 1, 0, 0, 0, 0).timestamp())
        last_timestamp = int(datetime(2019, 1, 1, 0, 0, 0, 0).timestamp())
        
        if (timestamp_begin > timestamp_end):
                self.date_end.errors.append('End date must be bigger than start date')
                result = False
        if (timestamp_begin < first_timestamp):
                self.date_end.errors.append('Start date must be bigger than 12.31.2017')
                result = False
        if (timestamp_end >= last_timestamp):
                self.date_end.errors.append('End date must be smaller than 01.01.2019')
                result = False
                
        return result


class StatForm(Form):
    date_begin = DateField('Start date:', [validators.InputRequired()], render_kw={"value": "2018-01-01"})
    date_end = DateField('End date:', [validators.InputRequired()], render_kw={"value": "2018-01-31"})
    #in_out = SelectField('International/Domestic:', choices = [('all', 'All'),
    #    ('international', 'International'), ('domestic', 'Domestic')])

    def validate(self):
        if not super().validate():
            return False
        result = True

        timestamp_begin = datetime.combine(self.date_begin.data, time.min).timestamp()
        timestamp_end = datetime.combine(self.date_end.data, time.max).timestamp()

        first_timestamp = int(datetime(2018, 1, 1, 0, 0, 0, 0).timestamp())
        last_timestamp = int(datetime(2019, 1, 1, 0, 0, 0, 0).timestamp())

        if (timestamp_begin > timestamp_end):
                self.date_end.errors.append('End date must be bigger than start date')
                result = False
        if (timestamp_begin < first_timestamp):
                self.date_end.errors.append('Start date must be bigger than 12.31.2017')
                result = False
        if (timestamp_end >= last_timestamp):
                self.date_end.errors.append('End date must be smaller than 01.01.2019')
                result = False

        return result
