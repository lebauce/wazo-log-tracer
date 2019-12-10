#!/usr/bin/python3


class Record:
    def __init__(
        self,
        id,
        method,
        uri,
        status,
        user_agent,
        service,
        record_time,
        request_start,
        request_duration,
        record_type,
    ):
        self.id = id
        self.method = method
        self.uri = uri
        self.status = status
        self.user_agent = user_agent
        self.service = service
        self.record_time = record_time
        self.request_start = request_start
        self.request_duration = request_duration
        self.type = record_type
