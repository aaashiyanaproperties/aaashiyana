def test_health_and_guest_search(client):
    assert client.get('/api/health').json()['status']=='ok'
    result=client.get('/api/properties').json()
    assert result['items']==[] and result['total']==0

def test_authenticated_property_lifecycle(client):
    headers={'X-Dev-User':'seller@example.test'}
    assert client.get('/api/me',headers=headers).status_code==200
    payload={'title':'Bright family apartment in Baner','description':'A thoughtfully planned home with natural light and easy access to local amenities.','transaction_type':'buy','property_type':'Apartment','city':'Pune','state':'Maharashtra','locality':'Baner','price':8500000,'bedrooms':2,'bathrooms':2,'carpet_area':1050,'status':'pending','amenities':['Gymnasium'],'images':[]}
    created=client.post('/api/properties',json=payload,headers=headers)
    assert created.status_code==200,created.text
    item=created.json(); assert item['status']=='pending'
    mine=client.get('/api/me/properties',headers=headers).json()
    assert len(mine)==1 and mine[0]['id']==item['id']
    deleted=client.delete('/api/properties/'+item['id'],headers=headers)
    assert deleted.status_code==200

def test_guest_cannot_publish_or_access_admin(client):
    payload={'title':'Bright family apartment in Baner','description':'A thoughtfully planned home with natural light and easy access to local amenities.','transaction_type':'buy','property_type':'Apartment','city':'Pune','state':'Maharashtra','locality':'Baner','price':8500000}
    assert client.post('/api/properties',json=payload).status_code==401
    assert client.get('/api/admin/overview',headers={'X-Dev-User':'seller@example.test'}).status_code==403

def test_inquiry_visit_favourite_and_admin_moderation(client):
    seller={'X-Dev-User':'workflow-seller@example.test'}
    payload={'title':'Sunny two bedroom residence in Pune','description':'An airy residence with a generous living room and practical access to transport, schools and daily essentials.','transaction_type':'buy','property_type':'Apartment','city':'Pune','state':'Maharashtra','locality':'Kharadi','price':11200000,'bedrooms':2,'bathrooms':2,'carpet_area':1150,'status':'pending','amenities':['Lift'],'images':[]}
    created=client.post('/api/properties',json=payload,headers=seller).json()
    client.get('/api/me',headers={'X-Dev-User':'workflow-admin@example.test'})
    from app.db.session import SessionLocal
    from app.models import User,UserRole
    db=SessionLocal()
    try:
        admin=db.query(User).filter_by(email='workflow-admin@example.test').first()
        db.add(UserRole(user_id=admin.id,role='admin'));db.commit()
    finally: db.close()
    admin_headers={'X-Dev-User':'workflow-admin@example.test'}
    moderated=client.post(f"/api/admin/properties/{created['id']}/moderate",json={'decision':'approve'},headers=admin_headers)
    assert moderated.status_code==200 and moderated.json()['status']=='published'
    saved=client.post(f"/api/properties/{created['id']}/favourite",headers=seller)
    assert saved.status_code==200 and saved.json()['saved'] is True
    inquiry=client.post(f"/api/properties/{created['id']}/inquiries",json={'name':'Buyer Example','email':'buyer@example.com','phone':'+919876543210','message':'Please share the floor plan and visit timings.','consent':True})
    assert inquiry.status_code==200
    from datetime import datetime,timedelta,timezone
    visit=client.post(f"/api/properties/{created['id']}/visits",json={'name':'Buyer Example','phone':'+919876543210','scheduled_at':(datetime.now(timezone.utc)+timedelta(days=2)).isoformat(),'consent':True})
    assert visit.status_code==200
    received=client.get('/api/me/inquiries',headers=seller)
    assert received.status_code==200 and len(received.json())==1

def test_draft_profile_contact_and_newsletter(client):
    headers={'X-Dev-User':'profile-owner@example.test'}
    draft=client.post('/api/properties/drafts',json={'city':'Pune','locality':'Baner'},headers=headers)
    assert draft.status_code==200 and draft.json()['status']=='draft'
    profile=client.patch('/api/me',json={'full_name':'Profile Owner','contact_phone':'+919876543210','bio':'Property owner profile'},headers=headers)
    assert profile.status_code==200 and profile.json()['contact_phone']=='+919876543210'
    contact=client.post('/api/contact-messages',json={'name':'Visitor','email':'visitor@example.com','topic':'General enquiry','message':'I would like to know more about Aashiyana.','consent':True})
    assert contact.status_code==200
    newsletter=client.post('/api/newsletter',json={'email':'subscriber@example.com','consent':True})
    assert newsletter.status_code==200 and newsletter.json()['subscribed'] is True
