# from barcode import uc_merced_mobile_id
# from send_code import send_otc
# import time
#
#
# class MobileID:
#     def __init__(self, user_cookie):
#         self.user_cookie = user_cookie
#
#         try:
#             info = uc_merced_mobile_id(user_cookie)
#         except Exception as e:
#             print(f"Error while parsing HTML content: {e}")
#
#         self.mobile_id_rand_array = info["mobile_id_rand_array"]
#         self.current_mobile_id_rand = 0
#         self.student_id = info["student_id"]
#         self.barcode = info["barcode"]
#
#     def __str__(self):
#         return (
#             f"MobileID(\n"
#             f"  student_id: {self.student_id},\n"
#             f"  barcode: {self.barcode},\n"
#             f"  current_mobile_id: {self.mobile_id_rand_array[self.current_mobile_id_rand] if self.mobile_id_rand_array else None},\n"
#             f"  mobile_id_rand_array: {self.mobile_id_rand_array}\n"
#             f")"
#         )
#
#     def get_user_info(self):
#         return {
#             "student_id": self.student_id,
#             "barcode": self.barcode,
#         }
#
#     def update(self):
#         info = uc_merced_mobile_id(self.user_cookie)
#         self.mobile_id_rand_array = info["mobile_id_rand_array"]
#         self.current_mobile_id_rand = 0
#         self.student_id = info["student_id"]
#         self.barcode = info["barcode"]
#
#     def generate(self):
#         max_retries = 3
#         attempt = 0
#         while attempt < max_retries:
#             # If we've exhausted the current mobile id array, update the information
#             if self.current_mobile_id_rand >= len(self.mobile_id_rand_array):
#                 self.update()
#             current = self.mobile_id_rand_array[self.current_mobile_id_rand]
#             send_code_result = send_otc(current, self.student_id, self.barcode)
#             if send_code_result["status"] == "success":
#                 return {
#                     "status": "success",
#                     "code": current,
#                     "response": send_code_result["response"],
#                 }
#             attempt += 1
#             self.current_mobile_id_rand += 1
#
#         return {
#             "status": "failed",
#             "code": current,
#             "response": send_code_result["response"],
#         }
#
#
# if __name__ == "__main__":
#     # Example usage
#     user_cookie = r"_scid=Ic_axybbNapcWu2KQbPQB0XUlkR3FPy2; _tt_enable_cookie=1; _ttp=01JN20PX96CN3HWEEDYE7SEZ03_.tt.1; _fbp=fb.1.1740603356486.499765120694379326; _mkto_trk=id:976-RKA-196&token:_mch-ucmerced.edu-bc9ac74da238b9517b062d67c0cf33be; _ga_MDV0RFSJ6H=GS1.1.1740731352.1.1.1740731475.0.0.0; _ga_TSE2LSBDQZ=GS1.1.1742426043.7.0.1742426043.60.0.0; _ga_ZNSTZ2YGVJ=GS1.1.1742529086.1.1.1742529115.0.0.0; _ga=GA1.2.510264552.1740603356; _gid=GA1.2.939168309.1743120107; _scid_r=M0_axybbNapcWu2KQbPQB0XUlkR3FPy2DKvtXg; _uetsid=23d4d9f00b8211f09342e9a3a7334d45; _uetvid=13366c10f48411efb8ba870ea856949e; _ScCbts=%5B%5D; _sctr=1%7C1743058800000; session_for%3Aindex_php=ST-1743136697376-36lj2wO4vhDV1sdr5tem6OHrM; _gat=1; _ga_12VFZGH5J2=GS1.2.1743151301.2.0.1743151301.0.0.0; _pk_ref.1.cb1f=%5B%22%22%2C%22%22%2C1743151306%2C%22https%3A%2F%2Fapi-70cee857.duosecurity.com%2F%22%5D; _pk_id.1.cb1f=da46508d627083ff.1742872489.5.1743151306.1743151306.; _pk_ses.1.cb1f=*"
#     mobile_id = MobileID(user_cookie)
#     # print(project_code)
#     # Generate and send the code
#     result = mobile_id.generate()
#     print(result)
