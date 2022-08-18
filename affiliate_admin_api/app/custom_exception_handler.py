from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    data = []
    data_item = {}
    if response:
        if response.status_code == 400:
            customized_response = {}
            for key, value in response.data.items():

                if isinstance(value, list):
                    customized_response[key] = str(value[0])
                else:
                    customized_response[key] = str(value)

            # if 'non_field_errors' in customized_response:
            #     customized_response['external_id'] = customized_response['non_field_errors']
                # del customized_response['non_field_errors']

            data_item['field_errors'] = customized_response
            data_item['non_field_errors'] = ''
            data.append(data_item)

            data_item = {}
            data_item['message'] = ''
            data.append(data_item)
            for key, item in customized_response.items():
                del response.data[key]

        else:
            data_item['message'] = response.data['detail']
            data.append(data_item)
            data_item = {}
            data_item['field_errors'] = {}
            data_item['non_field_errors'] = ''
            del response.data['detail']

            data.append(data_item)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['data'] = []
        response.data['url'] = "http://api.affiliate.dev.campus.com/admin/courses/"
        response.data['date_time'] = "2020-10-29T05:32:08.122577Z"
        response.data['status_code'] = response.status_code
        response.data['errors'] = data

    return response
