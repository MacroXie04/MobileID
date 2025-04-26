# UCMerced-Barcode

Welcome to the **UC Merced-Barcode**!

> This website is based Python Django framework and is designed to help student manage their **own** student card
> barcodes, including dynamic barcode and static barcode. It is **not capable** for stealing or accessing any other
> student's barcode without authorization. Please read the following legal disclaimer carefully to understand your
> rights
> and obligations when using this website.

---

## Legal Disclaimer

1. **Use at Your Own Risk**  
   This software is provided as a tool for students to manage their **own** barcodes. Users must ensure they possess the
   necessary technical understanding of how it works and acknowledge any potential risks. To the maximum extent
   permitted by applicable law, the developer (hereinafter “we”) assumes no liability for any direct or indirect
   consequences arising from the use of this software.

2. **No Warranties**  
   This software is provided on an “as is” basis, without any express or implied warranties, including (but not limited
   to) warranties of merchantability, fitness for a particular purpose, stability, or non-infringement. We do not
   guarantee that the software will function without interruptions or errors in all operating environments, nor do we
   guarantee that it will meet all your needs or expectations.

3. **Information & Data Security**  
   The software may store or process personal barcode data. Users are responsible for complying with all applicable
   privacy and data protection laws in their jurisdiction and for taking reasonable measures (e.g., encryption, backups,
   controlled access) to safeguard their data. We assume no responsibility for any data loss, leakage, or damage arising
   from third-party attacks, user negligence, or force majeure events.

4. **No Unauthorized Access**  
   This website/software cannot and does not steal or access any other user’s student card barcode. It only supports the
   import and management of **your own** barcode. Any attempt to use this software for illegal or unauthorized
   activities, including accessing others’ barcodes without permission, is strictly prohibited and solely the
   responsibility of the user engaging in such activities.

5. **Exclusion of Indirect Damages**  
   Under no circumstances shall we be liable for any indirect, incidental, consequential, or special damages (including,
   but not limited to, lost profits, business interruption, data loss, information leaks, reputational harm, or
   anticipated savings) arising out of or in connection with the use or inability to use this software, even if we have
   been advised of the possibility of such damages.

6. **User Compliance**  
   Users must ensure that their usage of this software aligns with all applicable laws, regulations, and institutional
   policies. Any violation of such requirements is the user’s responsibility. We bear no liability for any legal
   repercussions resulting from improper or unlawful use of the software.

7. **Third-Party Resources**  
   If this software contains links to third-party websites or services, these are provided merely for convenience. We
   make no representations or warranties regarding the accuracy, legality, or safety of any third-party resources and
   assume no liability for any consequences arising from their use.

8. **Governing Law & Dispute Resolution**  
   This disclaimer shall be governed by the applicable laws in your jurisdiction. Any dispute arising from the use of
   this software or interpretation of this disclaimer should first be attempted to be resolved amicably. If an amicable
   resolution cannot be reached, the dispute shall be submitted to the competent court in your locality.

9. **Modifications & Updates**  
   We reserve the right to update, modify, or discontinue this software and/or this disclaimer at any time without prior
   notice. Once updated, your continued use of the software signifies your acceptance of the revised terms.

---

## Features

- **UC Merced Dynamic Barcode Support**: The UC Merced dynamic barcode can be transfer **only under authorization** using the website build-in transfer toolkit.
- **UC Merced Dynamic Barcode Transfer Toolkit**: The UC Merced dynamic barcode transfer toolkit can be used to transfer the UC Merced dynamic barcode.

---

## Usage

### 1. Setup the Development Environment

```bash
   git clone https://github.com/your-username/UCMerced-Barcode.git
   cd UCMerced-Barcode
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
```

### 2. Database Migration

```bash
   python manage.py makemigrations mobileid
   python manage.py makemigrations webauthn_app
   python manage.py makemigrations
   python manage.py migrate
```

### 3. Run the Server

```bash
   python manage.py runserver
```






