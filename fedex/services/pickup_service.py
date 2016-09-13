from fedex.base_service import FedexBaseService


class FedexCreatePickupRequest(FedexBaseService):

    def __init__(self, config_obj, *args, **kwargs):
        self._config_obj = config_obj
        # Holds version info for the VersionId SOAP object.
        # NOTE: Update this with whatever updates from Fedex happen.
        self._version_info = {
            'service_id': 'disp',
            'major': '11',
            'intermediate': '0',
            'minor': '0'
        }
        self._package_length = kwargs.get('length')
        self._package_width = kwargs.get('width')
        self._package_height = kwargs.get('height')
        self._package_weight = kwargs.get('weight')

        self._number_of_business_days = kwargs.get('no_of_business_days')
        self._package_ready_time = kwargs.get('package_ready_time')
        self._custom_close_time = kwargs.get('custom_close_time')
        self._fedex_carrier_code = kwargs.get('fedex_carrier_code', 'FDXG')
        self._dispatch_date = kwargs.get('dispatch_date')
        self._service_type = kwargs.get('service_type', 'FEDEX_GROUND')
        self._packaging_type = kwargs.get('packaging_type', 'YOUR_PACKAGING')
        self._pickup_request_type = kwargs.get('pickup_request_type', 'FUTURE_DAY')

        self.OriginDetail = None
        self.PackageCount = None
        self.TotalWeight = None
        self.CarrierCode = None
        self.OversizePackageCount = None
        self.Remarks = None
        self.CommodityDescription = None
        self.CountryRelationship = None
        self.PickupServiceCategory = None
        super(FedexCreatePickupRequest, self).__init__(self._config_obj, 'PickupService_v11.wsdl', *args, **kwargs)

    def _prepare_wsdl_objects(self):
        self.OriginDetail = self.client.factory.create('PickupOriginDetail')
        self.OriginDetail.PickupLocation = self.client.factory.create('ContactAndAddress')
        self.OriginDetail.PickupLocation.Contact = self.client.factory.create('Contact')
        self.OriginDetail.PickupLocation.Address = self.client.factory.create('Address')
        self.OriginDetail.PackageLocation = None
        self.OriginDetail.BuildingPart = None

        self.TotalWeight = self.client.factory.create('Weight')

        self.CarrierCode = self.client.factory.create('CarrierCodeType')

        # Enable these for debugging
        # self.logger.debug(self.OriginDetail)
        # self.logger.debug(self.TotalWeight)
        # self.logger.debug(self.CarrierCode)

    def _assemble_and_send_request(self):
        """
        Fires off the Fedex request.

        @warning: NEVER CALL THIS METHOD DIRECTLY. CALL send_request(),
            WHICH RESIDES ON FedexBaseService AND IS INHERITED.
        """

        # Fire off the query.
        return self.client.service.createPickup(
            WebAuthenticationDetail=self.WebAuthenticationDetail,
            ClientDetail=self.ClientDetail,
            TransactionDetail=self.TransactionDetail,
            Version=self.VersionId,
            OriginDetail=self.OriginDetail,
            PickupServiceCategory=self.PickupServiceCategory,
            PackageCount=self.PackageCount,
            TotalWeight=self.TotalWeight,
            CarrierCode=self.CarrierCode,
            OversizePackageCount=self.OversizePackageCount,
            Remarks=self.Remarks,
            CommodityDescription=self.CommodityDescription,
            CountryRelationship=self.CountryRelationship
        )

    def get_availability(self):
        """Checks pickup availability. MAINLY to get CutOffTime."""

        # write the fields that are not already available:
        self.PickupType = 'ON_CALL'
        self.PickupAddress = self.OriginDetail.PickupLocation.Address
        # self.DispatchDate = self._dispatch_date  # Get from Merchant, from PickupRequest

        self.NumberOfBusinessDays = self._number_of_business_days  # From merchant or FedexEssentials
        self.PackageReadyTime = self._package_ready_time  # From merchant or FedexEssentials
        self.CustomerCloseTime = self._custom_close_time  # From merchant or FedexEssentials
        self.Carriers = self.client.factory.create(
            'CarrierCodeType')[self._fedex_carrier_code]  # From merchant or FedexEssentials

        ShipmentAttributes = self.client.factory.create('PickupShipmentAttributes')
        ShipmentAttributes.ServiceType = self.client.factory.create(
            'ServiceType')[self._service_type]
        ShipmentAttributes.PackagingType = self.client.factory.create('PackagingType')[self._packaging_type]
        ShipmentAttributes.Dimensions.Length = self._package_length
        ShipmentAttributes.Dimensions.Width = self._package_width
        ShipmentAttributes.Dimensions.Height = self._package_height
        ShipmentAttributes.Dimensions.Units = self.client.factory.create('LinearUnits').CM  # or IN
        ShipmentAttributes.Weight.Units = self.client.factory.create('WeightUnits').KG  # or LB
        ShipmentAttributes.Weight.Value = self._package_weight
        self.ShipmentAttributes = ShipmentAttributes

        AssociatedAccount = self.client.factory.create('AssociatedAccount')
        # AssociatedAccount.Type = ''  # Legacy account number, no need actually.
        AssociatedAccount.AccountNumber = self._config_obj.account_number
        self.AccountNumber = AssociatedAccount
        self.PickupRequestType = self.client.factory.create('PickupRequestType')[self._pickup_request_type]

        return self._get_availability()

    def _get_availability(self):
        # Fire off the query.
        return self.client.service.getPickupAvailability(
            WebAuthenticationDetail=self.WebAuthenticationDetail,
            ClientDetail=self.ClientDetail,
            TransactionDetail=self.TransactionDetail,  # optional
            Version=self.VersionId,

            # All of these are optional
            # Also in order as seen in pickup service WSDL
            PickupType=self.PickupType,
            AccountNumber=self.AccountNumber,
            PickupAddress=self.PickupAddress,
            PickupRequestType=self.PickupRequestType,
            # DispatchDate=self.DispatchDate,
            # NumberOfBusinessDays=self.NumberOfBusinessDays,  # positive integer
            # PackageReadyTime=self.PackageReadyTime,  # xs:time
            # CustomerCloseTime=self.CustomerCloseTime,  # xs:time
            Carriers=self.CarrierCode,
            ShipmentAttributes=self.ShipmentAttributes
        )
