import re
import json
import datetime
import uuid
import requests
from icalendar import Calendar, Event

def fetch_calendar_data(url):
    """Fetch ICS data from the provided URL"""
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def parse_terms(ics_data):
    """Parse the ICS data to extract term information"""
    calendar = Calendar.from_ical(ics_data)
    terms = []
    
    for component in calendar.walk('VEVENT'):
        summary = component.get('SUMMARY')
        # Extract term number using regex
        match = re.search(r'Term (\d+)', summary)
        if not match:
            continue
            
        term_number = int(match.group(1))
        start_date = component.get('DTSTART').dt
        end_date = component.get('DTEND').dt
        
        terms.append({
            'term_number': term_number,
            'start': start_date,
            'end': end_date,
            'summary': summary
        })
    
    return sorted(terms, key=lambda x: x['start'])

def generate_holidays(sorted_terms):
    """Generate holiday periods between consecutive terms"""
    # Map term numbers to holiday names
    holiday_names = {
        1: 'Oct Half Term',
        2: 'Christmas Holiday',
        3: 'Feb Half Term',
        4: 'Easter Holiday',
        5: 'May Half Term',
        6: 'Summer Holiday'
    }
    
    holidays = []
    
    # Process consecutive pairs of terms
    for i in range(len(sorted_terms) - 1):
        prev_term = sorted_terms[i]
        next_term = sorted_terms[i+1]
        
        # Get holiday name based on previous term number
        prev_term_number = prev_term['term_number']
        holiday_name = holiday_names.get(prev_term_number, f"Unknown Holiday after Term {prev_term_number}")
        
        # Calculate holiday period
        holiday_start = prev_term['end']
        holiday_end = next_term['start'] - datetime.timedelta(days=1)
        
        # Ensure valid date range
        if holiday_start <= holiday_end:
            holidays.append({
                'name': holiday_name,
                'start': holiday_start,
                'end': holiday_end
            })
    
    # Check for wrap-around from Term 6 to Term 1 of next year (Summer Holiday)
    if sorted_terms:
        last_term = sorted_terms[-1]
        if last_term['term_number'] == 6:
            next_year = last_term['end'].year + 1
            for term in sorted_terms:
                if term['term_number'] == 1 and term['start'].year == next_year:
                    holiday_start = last_term['end']
                    holiday_end = term['start'] - datetime.timedelta(days=1)
                    
                    if holiday_start <= holiday_end:
                        holidays.append({
                            'name': holiday_names[6],  # Summer Holiday
                            'start': holiday_start,
                            'end': holiday_end
                        })
                    break
    
    return holidays

def write_json_output(holidays, filename='holidays.json'):
    """Write holidays to JSON file"""
    json_output = []
    for holiday in holidays:
        json_output.append({
            'name': holiday['name'],
            'start': holiday['start'].isoformat(),
            'end': holiday['end'].isoformat()
        })
    
    with open(filename, 'w') as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    
    print(f"JSON output written to {filename}")

def write_ics_output(holidays, filename='holidays.ics'):
    """Write holidays to ICS file"""
    cal = Calendar()
    cal.add('prodid', '-//School Holidays//generated//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', 'Gloucestershire School Holidays')
    cal.add('x-wr-timezone', 'UTC')
    
    for holiday in holidays:
        event = Event()
        event.add('summary', holiday['name'])
        
        # Set start and end dates (end date is exclusive in ICS)
        start_date = holiday['start']
        end_date = holiday['end'] + datetime.timedelta(days=1)
        
        event.add('dtstart', start_date)
        event.add('dtend', end_date)
        
        # Ensure dates are treated as all-day events
        event['dtstart'].params['value'] = 'DATE'
        event['dtend'].params['value'] = 'DATE'
        
        # Add other required fields
        event.add('dtstamp', datetime.datetime.now(datetime.timezone.utc))
        event.add('uid', str(uuid.uuid4()))
        event.add('class', 'PUBLIC')
        event.add('created', datetime.datetime.now(datetime.timezone.utc))
        event.add('description', '')
        event.add('last-modified', datetime.datetime.now(datetime.timezone.utc))
        event.add('sequence', 0)
        event.add('status', 'CONFIRMED')
        event.add('transp', 'TRANSPARENT')
        
        cal.add_component(event)
    
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())
    
    print(f"ICS output written to {filename}")

def main():
    url = 'https://calendar.google.com/calendar/ical/mv20jri1aefq8qfsetmiui9thk%40group.calendar.google.com/public/basic.ics'
    
    try:
        # Fetch and process data
        ics_data = fetch_calendar_data(url)
        sorted_terms = parse_terms(ics_data)
        holidays = generate_holidays(sorted_terms)
        
        # Write output files
        write_json_output(holidays)
        write_ics_output(holidays)
        
        print(f"Processed {len(sorted_terms)} terms and generated {len(holidays)} holidays")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
