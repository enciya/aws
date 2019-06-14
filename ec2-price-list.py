import boto3
import csv
import json
import pprint


class EC2PriceParser:

    columns_headers = ["instanceType", "instanceFamily", "operatingSystem", "vcpu", "memory", "pricingModel", "groupCode",
                      "rateCode", "description", "pricePerUnit", "unit", "tenancy", "OfferingClass", "LeaseContractLength",
                      "PurchaseOption"]

    def __init__(self, file_name):
        self.file_name = file_name

    def parse(self):
        try:
            with open(self.file_name, 'w') as outfile:
                self.csv_writer = csv.writer(outfile, lineterminator='\n')
                self.csv_writer.writerow(self.columns_headers)
                self.parse_price()
        except Exception as error:
            print error

    def parse_price(self):
        pricing_client = boto3.client('pricing', region_name='us-east-1')
        search_filter = [{'Type': 'TERM_MATCH', 'Field': 'location',  'Value': 'EU (Ireland)'}]
        marker = None
        while True:
            if marker:
                response_iterator = pricing_client.get_products(ServiceCode='AmazonEC2',
                                                         Filters=search_filter,
                                                         MaxResults=100,
                                                         NextToken=marker)
            else:
                response_iterator = pricing_client.get_products(ServiceCode='AmazonEC2',
                                                         Filters=search_filter,
                                                         MaxResults=100)

            self.parse_product(response_iterator)

            try:
                marker = response_iterator['NextToken']
                print marker
            except KeyError:
                break

    def parse_product(self, response_iterator):

            for price in response_iterator['PriceList']:

                pp = pprint.PrettyPrinter(indent=1, width=300)
                pobject = json.loads(price)
                dict = pobject['product']['attributes']

                print ("Service Code :" + pobject['serviceCode'])
                print ("Publication date :"+pobject['publicationDate'])

                instanceType = dict['instanceType'] if dict.get("instanceType") != None else ""
                instanceFamily = dict['instanceFamily'] if dict.get("instanceFamily") != None else ""
                operatingSystem = dict['operatingSystem'] if dict.get("operatingSystem") != None else ""
                vcpu = dict['vcpu'] if dict.get("vcpu") != None else ""
                memory = dict['memory'] if dict.get("memory") != None else ""
                tenancy = dict['tenancy'] if dict.get("tenancy") != None else ""

                dictTerms = pobject['terms']
                onDemand_dict = dictTerms['OnDemand'] if dictTerms.get("OnDemand") != None else {}
                self.iterate_terms("OnDemand", dict, instanceFamily, instanceType, memory, onDemand_dict, operatingSystem,
                                   tenancy, vcpu)

                reserved_dict = dictTerms['Reserved'] if dictTerms.get("Reserved") != None else {}
                self.iterate_terms("reserved", dict, instanceFamily, instanceType, memory, reserved_dict, operatingSystem,
                                   tenancy, vcpu)
                pp.pprint(pobject)


    def iterate_terms(self, ptype, dict, instanceFamily, instanceType, memory, terms_dict, operatingSystem, tenancy, vcpu):
        for k, v in terms_dict.iteritems():
            if type(v) == type(dict):
                termAttrDict = v
                for kk, vv in termAttrDict["priceDimensions"].iteritems():
                    if type(vv) == type(dict):
                        deepDict = vv
                        rateCode = deepDict['rateCode']
                        a, b, c = rateCode.split(".")
                        groupCode = a + "." + b
                        description = deepDict['description']
                        pricePerUnit = deepDict['pricePerUnit']['USD']
                        unit = deepDict['unit']

                        leaseContractLength = offeringClass = purchaseOption = ""

                        if termAttrDict['termAttributes'] != {}:
                            leaseContractLength = termAttrDict['termAttributes']["LeaseContractLength"]
                            offeringClass = termAttrDict['termAttributes']["OfferingClass"]
                            purchaseOption = termAttrDict['termAttributes']["PurchaseOption"]

                        self.csv_writer.writerow(
                            [instanceType, instanceFamily, operatingSystem, vcpu, memory, ptype, groupCode,
                             rateCode, description, pricePerUnit, unit, tenancy, offeringClass, leaseContractLength,
                             purchaseOption])
                print(v)
            else:
                print "{0} : {1}".format(k, v)


if __name__ == "__main__":
    ec2_price_parser= EC2PriceParser('csv\EC2IrlandaPrices.csv')
    ec2_price_parser.parse()
